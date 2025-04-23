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

        local_thread = thread
        if self.fork_history:
            local_history = await self._build_history(thread)
            local_thread = ChatHistoryAgentThread(local_history)

        while not self.is_complete:
            # Create a plan based on the current history and feedback (if any)
            local_history = await self._build_history(thread)
            plan = await self.planning_strategy.create_plan(
                self.agents, local_history.messages, feedback
            )

            for step in plan.plan:
                # Pick next agent to execute the step
                selected_agent = next(
                    agent for agent in self.agents if agent.id == step.agent_id
                )
                # And add the step instructions to the history
                step_instructions = ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    name=self.id,
                    content=step.instructions,
                )

                async for response in selected_agent.invoke(
                    messages=[step_instructions],
                    thread=local_thread,
                ):
                    message = response.message
                    logger.debug(f"Agent '{selected_agent.id}' sent message: {message}")

                    yield message

            # Provide feedback and check if the plan can complete
            ok, feedback = await self.feedback_strategy.provide_feedback(
                local_history.messages
            )
            self.is_complete = ok

        # Merge the history if needed
        if self.fork_history:
            logger.debug("Merging history after plan execution")
            local_history = await self._build_history(local_thread)
            source_history = await self._build_history(thread)
            delta = await self.merge_strategy.merge(
                source_history.messages, local_history.messages
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
    async def _inner_invoke_stream(
        self,
        *,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:

        # In case the agent is invoked multiple times
        self.is_complete = False
        feedback: str = ""

        local_thread = thread
        if self.fork_history:
            local_history = await self._build_history(thread)
            local_thread = ChatHistoryAgentThread(local_history, thread_id=f"fork_{thread.id}")

        while not self.is_complete:
            # Create a plan based on the current history and feedback (if any)
            local_history = await self._build_history(thread)
            plan = await self.planning_strategy.create_plan(
                self.agents, local_history.messages, feedback
            )

            for step in plan.plan:
                # Pick next agent to execute the step
                selected_agent = next(
                    agent for agent in self.agents if agent.id == step.agent_id
                )
                # And add the step instructions to the history
                step_instructions = ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    name=self.id,
                    content=step.instructions,
                )

                message = None
                # TODO: when forking history, do we need to still yield intermediate messages?
                async for response in selected_agent.invoke_stream(
                    messages=[step_instructions], thread=local_thread
                ):
                    chunk = response.message

                    yield chunk

                    message = await self._collect_chunks(chunk, message, thread)

            local_history = await self._build_history(thread)
            ok, feedback = await self.feedback_strategy.provide_feedback(
                local_history.messages
            )
            self.is_complete = ok

        if self.fork_history:
            logger.debug("Merging history after plan execution")
            local_history = await self._build_history(local_thread)
            source_history = await self._build_history(thread)
            delta = await self.merge_strategy.merge(
                source_history.messages, local_history.messages
            )

            # Yield the merged history delta and update the thread
            for d in delta:
                # In this case, we simply state the message is from the team and not from a specific agent
                d.name = self.id
                await thread.on_new_message(d)
