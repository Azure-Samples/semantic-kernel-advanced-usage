import logging

from collections.abc import AsyncIterable
from typing import Any, ClassVar
import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover
from semantic_kernel.agents import Agent
from semantic_kernel.agents.strategies.selection.selection_strategy import (
    SelectionStrategy,
)
from semantic_kernel.agents.strategies.termination.termination_strategy import (
    TerminationStrategy,
)
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_invocation,
    trace_agent_get_response,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException

logger: logging.Logger = logging.getLogger(__name__)


class Team(Agent):
    """
    A team of agents that can work together to solve a problem.

    Arguments:
        id: The ID of the team.
        description: The description of the team.
        agents: The agents in the team.
        selection_strategy: The strategy for selecting which agent to use.
        termination_strategy: The strategy for determining when to stop the team.
    """

    id: str
    description: str
    agents: list[Agent]
    selection_strategy: SelectionStrategy
    termination_strategy: TerminationStrategy
    channel_type: ClassVar[type[AgentChannel]] = ChatHistoryChannel
    is_complete: bool = False

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

        # Channel required to communicate with agents
        channel = await self.create_channel()
        await channel.receive(history.messages)

        # TODO: check if it makes sense to have a termination strategy here
        for _ in range(self.termination_strategy.maximum_iterations):
            try:
                selected_agent = await self.selection_strategy.next(
                    self.agents, history.messages
                )
            # TODO: possible handle a case when no agent is selected
            except Exception as ex:
                logger.error(f"Failed to select agent: {ex}")
                raise AgentChatException("Failed to select agent") from ex

            async for is_visible, message in channel.invoke(selected_agent):
                history.add_message(message)
                logger.info(f"Agent {selected_agent.id} sent message: {message}")
                if message.role == AuthorRole.ASSISTANT:
                    task = self.termination_strategy.should_terminate(
                        selected_agent, history.messages
                    )
                    self.is_complete = await task

                if is_visible:
                    yield message

            if self.is_complete:
                break

    @trace_agent_invocation
    async def invoke_stream(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[StreamingChatMessageContent]:
        # TODO REVIEW!!

        # Channel required to communicate with agents
        channel = await self.create_channel()
        await channel.receive(history.messages)

        # TODO: check if it makes sense to have a termination strategy here
        for _ in range(self.termination_strategy.maximum_iterations):
            try:
                selected_agent = await self.selection_strategy.next(
                    self.agents, history.messages
                )
            # TODO: possible handle a case when no agent is selected
            except Exception as ex:
                logger.error(f"Failed to select agent: {ex}")
                raise AgentChatException("Failed to select agent") from ex

            messages: list[ChatMessageContent] = []

            async for message in channel.invoke_stream(selected_agent, messages):
                yield message

            for message in messages:
                history.messages.append(message)
