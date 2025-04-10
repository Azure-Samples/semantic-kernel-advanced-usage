from abc import ABC
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
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_invocation,
    trace_agent_get_response,
)
from semantic_kernel.contents import (
    ChatHistory,
    ChatMessageContent,
    StreamingChatMessageContent,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException

logger: logging.Logger = logging.getLogger(__name__)


class TeamBase(Agent, ABC):
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
            thread,
            chat_history,
            None,
            arguments,
            kernel,
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

        async for response in self._inner_invoke(
            thread=thread,
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
        pass

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
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]: ...

    async def create_channel(
        self, chat_history: ChatHistory | None = None, thread_id: str | None = None
    ) -> AgentChannel:
        """Create a ChatHistoryChannel.

        Args:
            chat_history: The chat history for the channel. If None, a new ChatHistory instance will be created.
            thread_id: The ID of the thread. If None, a new thread will be created.

        Returns:
            An instance of AgentChannel.
        """
        from semantic_kernel.agents.chat_completion.chat_completion_agent import (
            ChatHistoryAgentThread,
        )

        ChatHistoryChannel.model_rebuild()

        thread = ChatHistoryAgentThread(chat_history=chat_history, thread_id=thread_id)

        if thread.id is None:
            await thread.create()

        messages = [message async for message in thread.get_messages()]

        return ChatHistoryChannel(messages=messages, thread=thread)

    def _get_agent_hash(self, agent: Agent):
        """Get the hash of an agent."""
        hash_value = self.channel_map.get(agent, None)
        if hash_value is None:
            hash_value = KeyEncoder.generate_hash(agent.get_channel_keys())
            self.channel_map[agent] = hash_value

        return hash_value

    async def _build_history(self, thread: ChatHistoryAgentThread) -> ChatHistory:
        """Build the history."""
        chat_history = ChatHistory()
        async for message in thread.get_messages():
            chat_history.add_message(message)
        return chat_history

    async def _get_or_create_channel(
        self, agent: Agent, messages: list[ChatMessageContent]
    ) -> AgentChannel:
        """Get or create a channel."""
        channel_key = self._get_agent_hash(agent)
        channel = self.agent_channels.get(channel_key, None)
        if channel is None:
            channel = await agent.create_channel()
            self.agent_channels[channel_key] = channel

            if len(messages) > 0:
                await channel.receive(messages)
        return channel
