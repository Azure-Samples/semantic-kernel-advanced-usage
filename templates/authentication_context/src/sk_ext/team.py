import logging

from collections.abc import AsyncIterable
from typing import Any, Awaitable, Callable
import sys

from .team_base import TeamBase

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover
from semantic_kernel import Kernel
from semantic_kernel.agents import (
    ChatHistoryAgentThread,
    AgentResponseItem,
    AgentThread,
)
from semantic_kernel.agents.strategies.selection.selection_strategy import (
    SelectionStrategy,
)
from semantic_kernel.agents.strategies.termination.termination_strategy import (
    TerminationStrategy,
)
from semantic_kernel.contents import (
    ChatMessageContent,
    StreamingChatMessageContent,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException

logger: logging.Logger = logging.getLogger(__name__)


class Team(TeamBase):
    """
    A team of agents that can work together to solve a problem.

    Arguments:
        id: The ID of the team.
        description: The description of the team.
        agents: The agents in the team.
        selection_strategy: The strategy for selecting which agent to use.
        termination_strategy: The strategy for determining when to stop the team.
    """

    selection_strategy: SelectionStrategy
    termination_strategy: TerminationStrategy
    is_complete: bool = False

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

        # TODO: check if it makes sense to have a termination strategy here
        for _ in range(self.termination_strategy.maximum_iterations):
            # Get the history of the thread
            history = await self._build_history(thread)

            # Perform next agent selection
            try:
                selected_agent = await self.selection_strategy.next(
                    self.agents, history=history.messages
                )
            except Exception as ex:
                logger.error(f"Failed to select agent: {ex}")
                raise AgentChatException("Failed to select agent") from ex

            async for response in selected_agent.invoke(
                thread=thread,
            ):
                message = response.message
                logger.debug(f"Agent '{selected_agent.id}' sent message: {message}")

                yield message

                # Check for termination
                # TODO check after each message or after each agent invocation?
                if message.role == AuthorRole.ASSISTANT:
                    task = self.termination_strategy.should_terminate(
                        selected_agent, thread._chat_history.messages
                    )
                    self.is_complete = await task

            if self.is_complete:
                break

    @override
    async def _inner_invoke_stream(
        self,
        thread: AgentThread | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        # In case the agent is invoked multiple times
        self.is_complete = False

        # TODO: check if it makes sense to have a termination strategy here
        for _ in range(self.termination_strategy.maximum_iterations):
            # Get the history of the thread
            history = await self._build_history(thread)

            # Perform next agent selection
            try:
                selected_agent = await self.selection_strategy.next(
                    self.agents, history=history.messages
                )
            except Exception as ex:
                logger.error(f"Failed to select agent: {ex}")
                raise AgentChatException("Failed to select agent") from ex

            # NOTE: an agent can produce multiple messages in a single invocation
            message = None
            async for response in selected_agent.invoke_stream(
                thread=thread,
            ):
                chunk = response.message
                logger.info(f"Agent {selected_agent.id} sent chunk: {chunk}")

                yield chunk

                if message is None:
                    message = chunk
                elif chunk.role == message.role:
                    message += chunk
                else:
                    # Update the thread with the new message
                    await thread.on_new_message(message)

            # Check for termination
            task = self.termination_strategy.should_terminate(
                selected_agent, history.messages
            )
            self.is_complete = await task

            if self.is_complete:
                break
