import logging

from collections.abc import AsyncIterable
from typing import Any, ClassVar
import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents import Agent
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_invocation,
    trace_agent_get_response,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException

from sk_ext.feedback_strategy import FeedbackStrategy
from sk_ext.planning_strategy import PlanningStrategy
from sk_ext.merge_strategy import MergeHistoryStrategy

logger = logging.getLogger(__name__)


class PlannedTeam(Agent):
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

    id: str
    description: str
    agents: list[Agent]
    planning_strategy: PlanningStrategy
    feedback_strategy: FeedbackStrategy
    channel_type: ClassVar[type[AgentChannel]] = ChatHistoryChannel
    is_complete: bool = False
    fork_history: bool = False
    merge_strategy: MergeHistoryStrategy = None

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> ChatMessageContent:
        """Get a response from the agent.

        Args:
            history: The chat history.
            arguments: The kernel arguments. (optional)
            kernel: The kernel instance. (optional)
            kwargs: The keyword arguments. (optional)

        Returns:
            A chat message content.
        """
        responses: list[ChatMessageContent] = []
        async for response in self._inner_invoke(history, arguments, kernel, **kwargs):
            responses.append(response)

        if not responses:
            raise AgentInvokeException("No response from agent.")

        return responses[0]

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the chat history handler.

        Args:
            history: The chat history.
            arguments: The kernel arguments.
            kernel: The kernel instance.
            kwargs: The keyword arguments.

        Returns:
            An async iterable of ChatMessageContent.
        """
        async for response in self._inner_invoke(history, arguments, kernel, **kwargs):
            yield response

    async def _inner_invoke(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        # In case the agent is invoked multiple times
        self.is_complete = False
        feedback: str = ""

        local_history = (
            history
            if not self.fork_history
            # When forking history, we need to create a new copy of ChatHistory
            else ChatHistory(
                system_message=history.system_message, messages=history.messages.copy()
            )
        )

        # Channel required to communicate with agents
        channel = await self.create_channel()
        await channel.receive(local_history.messages)

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

                # Then invoke the agent
                async for is_visible, message in channel.invoke(selected_agent):
                    local_history.add_message(message)

                    if is_visible and not self.fork_history:
                        # If we are not forking history, we can yield the message
                        # This prevents forked message to appear in the main history
                        yield message

            # Provide feedback and check if the plan can complete
            ok, feedback = await self.feedback_strategy.provide_feedback(
                local_history.messages
            )
            self.is_complete = ok

        # Merge the history if needed
        if self.fork_history:
            logger.debug("Merging history after iteration")
            delta = await self.merge_strategy.merge(
                history.messages, local_history.messages
            )

            # Yield the merged history delta
            for d in delta:
                yield d

    @trace_agent_invocation
    async def invoke_stream(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamingChatMessageContent]:
        # In case the agent is invoked multiple times
        self.is_complete = False
        feedback: str = ""

        local_history = (
            history
            if not self.fork_history
            # When forking history, we need to create a new copy of ChatHistory
            else ChatHistory(
                system_message=history.system_message, messages=history.messages.copy()
            )
        )

        # Channel required to communicate with agents
        channel = await self.create_channel()
        await channel.receive(local_history.messages)

        while not self.is_complete:
            plan = await self.planning_strategy.create_plan(
                self.agents, local_history.messages, feedback
            )

            for step in plan.plan:
                selected_agent = next(
                    agent for agent in self.agents if agent.id == step.agent_id
                )
                history.add_message(
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        name=self.id,
                        content=step.instructions,
                    )
                )

                messages: list[ChatMessageContent] = []

                # TODO: when forking history, do we need to still yield intermediate messages?
                async for message in channel.invoke_stream(selected_agent, messages):
                    yield message

                for message in messages:
                    local_history.messages.append(message)

            ok, feedback = await self.feedback_strategy.provide_feedback(
                local_history.messages
            )
            self.is_complete = ok
