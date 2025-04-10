import logging

from collections.abc import AsyncIterable
from typing import Any, Awaitable, Callable, ClassVar
import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover
from pydantic import Field
from semantic_kernel import Kernel
from semantic_kernel.agents import (
    Agent,
    AgentThread,
    AgentResponseItem,
    ChatHistoryAgentThread,
)
from semantic_kernel.agents.group_chat.agent_chat_utils import KeyEncoder
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
    agent_channels: dict[str, AgentChannel] = Field(default_factory=dict)
    channel_map: dict[Agent, str] = Field(default_factory=dict)
    is_complete: bool = False

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        *,
        messages: (
            str | ChatMessageContent | list[str | ChatMessageContent] | None
        ) = None,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Get a response from the agent.

        Args:
            history: The chat history.
            arguments: The kernel arguments. (optional)
            kernel: The kernel instance. (optional)
            kwargs: The keyword arguments. (optional)

        Returns:
            A chat message content.
        """
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

        responses: list[ChatMessageContent] = []
        async for response in self._inner_invoke(
            history=chat_history,
            arguments=arguments,
            kernel=kernel,
            on_intermediate_message=None,
            **kwargs,
        ):
            responses.append(response)

        if not responses:
            raise AgentInvokeException("No response from agent.")

        return AgentResponseItem(message=responses[-1], thread=thread)

    @trace_agent_invocation
    @override
    async def invoke(
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
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """Invoke the chat history handler.

        Args:
            history: The chat history.
            arguments: The kernel arguments.
            kernel: The kernel instance.
            kwargs: The keyword arguments.

        Returns:
            An async iterable of ChatMessageContent.
        """
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

        async for response in self._inner_invoke(
            thread=thread,
            history=chat_history,
            arguments=arguments,
            kernel=kernel,
            on_intermediate_message=on_intermediate_message,
            **kwargs,
        ):
            yield AgentResponseItem(message=response, thread=thread)

    async def _inner_invoke(
        self,
        thread: ChatHistoryAgentThread,
        history: ChatHistory,
        on_intermediate_message: (
            Callable[[ChatMessageContent], Awaitable[None]] | None
        ) = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        # In case the agent is invoked multiple times
        self.is_complete = False

        # TODO: check if it makes sense to have a termination strategy here
        for _ in range(self.termination_strategy.maximum_iterations):
            try:
                selected_agent = await self.selection_strategy.next(
                    self.agents, history=history
                )
            # TODO: possible handle a case when no agent is selected
            except Exception as ex:
                logger.error(f"Failed to select agent: {ex}")
                raise AgentChatException("Failed to select agent") from ex

            # Channel required to communicate with agents
            channel = await self._get_or_create_channel(selected_agent, history)

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

    def _get_agent_hash(self, agent: Agent):
        """Get the hash of an agent."""
        hash_value = self.channel_map.get(agent, None)
        if hash_value is None:
            hash_value = KeyEncoder.generate_hash(agent.get_channel_keys())
            self.channel_map[agent] = hash_value

        return hash_value

    async def _get_or_create_channel(
        self, agent: Agent, history: ChatHistory
    ) -> AgentChannel:
        """Get or create a channel."""
        channel_key = self._get_agent_hash(agent)
        channel = self.agent_channels.get(channel_key, None)
        if channel is None:
            channel = await agent.create_channel()
            self.agent_channels[channel_key] = channel

            if len(history.messages) > 0:
                await channel.receive(history.messages)
        return channel
