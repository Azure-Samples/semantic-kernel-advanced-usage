import logging

from collections.abc import AsyncIterable
from typing import Any, Awaitable, Callable
import sys

from .team_base import TeamBase

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.kernel import Kernel
from semantic_kernel.agents import (
    ChatHistoryAgentThread,
    AgentResponseItem,
    AgentThread,
)
from semantic_kernel.contents import (
    ChatHistory,
    ChatMessageContent,
    AuthorRole,
    StreamingChatMessageContent,
)
from semantic_kernel.functions import KernelArguments

from sk_ext.feedback_strategy import FeedbackStrategy
from sk_ext.planning_strategy import PlanningStrategy
from sk_ext.merge_strategy import MergeHistoryStrategy

logger = logging.getLogger(__name__)


class PlannedTeam(TeamBase):
    """A team of agents that executes a plan in a coordinated manner.

    Args:
        id (str): The id of the team.
        description (str): The description of the team.
        agents (list[Agent]): The agents that are part of the team.
        planning_strategy (PlanningStrategy): The strategy used to define the execution plan.
        feedback_strategy (FeedbackStrategy): The strategy used to provide feedback to the plan and reiterate if needed.
        channel_type (type[AgentChannel], optional): The channel type used to communicate with the agents. Defaults to ChatHistoryChannel.
        is_complete (bool, optional): Whether the team has completed its plan. Defaults to False.
        fork_history (bool, optional): Whether to fork the history for each iteration. Defaults to False.
        merge_strategy (MergeHistoryStrategy): The strategy used to merge the history after each iteration.
    """

    planning_strategy: PlanningStrategy
    feedback_strategy: FeedbackStrategy
    is_complete: bool = False
    fork_history: bool = False
    merge_strategy: MergeHistoryStrategy = None

    @override
    async def _inner_invoke(
        self,
        thread: ChatHistoryAgentThread,
        on_intermediate_message: (
            Callable[[ChatMessageContent], Awaitable[None]] | None
        ) = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        # In case the agent is invoked multiple times
        self.is_complete = False
        feedback: str = ""

        history = await self._build_history(thread)
        local_history = (
            history
            if not self.fork_history
            # When forking history, we need to create a new copy of ChatHistory
            else ChatHistory(
                system_message=history.system_message, messages=history.messages.copy()
            )
        )

        while not self.is_complete:
            # Create a plan based on the current history and feedback (if any)
            plan = await self.planning_strategy.create_plan(
                self.agents, local_history.messages, feedback
            )

            for step in plan.plan:
                # Pick next agent to execute the step
                selected_agent = next(
                    agent for agent in self.agents if agent.id == step.agent_id
                )
                # And add the step instructions to the history
                local_history.add_message(
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        name=self.id,
                        content=step.instructions,
                    )
                )

                # Channel required to communicate with agents
                channel = await self._get_or_create_channel(
                    selected_agent, local_history
                )
                # NOTE: an agent can produce multiple messages in a single invocation
                async for is_visible, message in channel.invoke(selected_agent):
                    # Keep updating local history
                    # NOTE: this is a local history, not the one in the thread
                    message.name = selected_agent.id
                    local_history.add_message(message)

                    if not self.fork_history:
                        # If we are not forking history, we need to update the thread with the new message
                        await thread.on_new_message(message)
                        if on_intermediate_message:
                            await on_intermediate_message(message)

                    if is_visible and not self.fork_history:
                        # If we are not forking history, we can yield the message now
                        # This prevents forked message to appear in the main history
                        yield message

            # Provide feedback and check if the plan can complete
            ok, feedback = await self.feedback_strategy.provide_feedback(
                local_history.messages
            )
            self.is_complete = ok

        # Merge the history if needed
        if self.fork_history:
            logger.debug("Merging history after plan execution")
            delta = await self.merge_strategy.merge(
                history.messages, local_history.messages
            )

            # Yield the merged history delta and update the thread
            for d in delta:
                # In this case, we simply state the message is from the team and not from a specific agent
                d.name = self.id
                await thread.on_new_message(d)
                if on_intermediate_message:
                    await on_intermediate_message(d)
                yield d

    @override
    async def invoke_stream(
        self,
        *,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        thread: AgentThread | None = None,
        on_intermediate_message: (
            Callable[[ChatMessageContent], Awaitable[None]] | None
        ) = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: ChatHistoryAgentThread(),
            expected_type=ChatHistoryAgentThread,
        )
        assert thread.id is not None  # nosec

        chat_history = ChatHistory()
        async for message in thread.get_messages():
            chat_history.add_message(message)

        # In case the agent is invoked multiple times
        self.is_complete = False
        feedback: str = ""

        local_history = (
            chat_history
            if not self.fork_history
            # When forking history, we need to create a new copy of ChatHistory
            else ChatHistory(
                system_message=chat_history.system_message,
                messages=chat_history.messages.copy(),
            )
        )

        while not self.is_complete:
            plan = await self.planning_strategy.create_plan(
                self.agents, local_history.messages, feedback
            )

            for step in plan.plan:
                selected_agent = next(
                    agent for agent in self.agents if agent.id == step.agent_id
                )
                local_history.add_message(
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        name=self.id,
                        content=step.instructions,
                    )
                )

                messages: list[ChatMessageContent] = []

                # Channel required to communicate with agents
                channel = await self._get_or_create_channel(
                    selected_agent, local_history
                )
                # TODO: when forking history, do we need to still yield intermediate messages?
                async for message in channel.invoke_stream(selected_agent, messages):
                    yield message

                for message in messages:
                    local_history.messages.append(message)

            ok, feedback = await self.feedback_strategy.provide_feedback(
                local_history.messages
            )
            self.is_complete = ok
