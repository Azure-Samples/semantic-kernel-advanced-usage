import logging
from typing import Any, AsyncIterable

import aiohttp

from semantic_kernel.agents import Agent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException

logger = logging.getLogger(__name__)


class DirectLineAgent(Agent):
    """
    An Agent subclass that connects to a DirectLine Bot from Microsoft Bot Framework.
    """

    def __init__(
        self,
        *,
        directline_secret: str,
        bot_endpoint: str,
        conversation_id: str | None = None,
        name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the DirectLineAgent.

        Args:
            directline_secret (str): The DirectLine secret used for authentication.
            bot_endpoint (str): The DirectLine endpoint URL for sending messages.
            conversation_id (str, optional): A conversation ID to resume conversation.
            name (str, optional): The name of the agent.
            kwargs: Other keyword arguments to pass to the base Agent.
        """
        super().__init__(name=name, **kwargs)
        self.directline_secret = directline_secret
        self.bot_endpoint = bot_endpoint
        self.conversation_id = conversation_id
        self.session = aiohttp.ClientSession()

    async def get_response(
        self,
        history: ChatHistory,
        arguments: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ChatMessageContent:
        """
        Get a response from the DirectLine Bot.

        Args:
            history: The chat history.
            arguments: Additional message arguments (optional).
            kwargs: Other keyword arguments.

        Returns:
            A ChatMessageContent response.
        """
        responses = []
        async for response in self.invoke(history, arguments, **kwargs):
            responses.append(response)

        if not responses:
            raise AgentInvokeException("No response from DirectLine Bot.")

        return responses[0]

    async def invoke(
        self,
        history: ChatHistory,
        arguments: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """
        Send the latest message in the chat history to the DirectLine Bot and yield any responses.

        Args:
            history: The chat history.
            arguments: Additional message arguments (optional).
            kwargs: Other keyword arguments.

        Yields:
            ChatMessageContent: The responses from the DirectLine Bot.
        """
        payload = self._build_payload(history, arguments, **kwargs)
        response_data = await self._send_message(payload)
        if response_data is None or "activities" not in response_data:
            raise AgentInvokeException("Invalid response from DirectLine Bot.")

        for activity in response_data["activities"]:
            message = ChatMessageContent(
                role=activity.get("from", {}).get("role", "bot"),
                content=activity.get("text", ""),
                name=self.name,
            )
            yield message

    def _build_payload(
        self,
        history: ChatHistory,
        arguments: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Build the message payload for the DirectLine Bot.

        In this example the latest message from the user is sent.
        You can customize this method to include additional context from the history or arguments.

        Args:
            history: The chat history.
            arguments: Additional message arguments (optional).
            kwargs: Other keyword arguments.

        Returns:
            A dictionary representing the message payload.
        """
        # Use the last message from the history as the message to send.
        latest_message = history.messages[-1] if history.messages else None
        text = latest_message.content if latest_message else "Hello"
        return {
            "type": "message",
            "from": {"id": "user"},
            "text": text,
        }

    async def _send_message(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Send the payload to the DirectLine Bot endpoint using the stored secret.

        Args:
            payload: The JSON payload to send.

        Returns:
            The JSON response from the DirectLine Bot if successful, otherwise None.
        """
        headers = {
            "Authorization": f"Bearer {self.directline_secret}",
            "Content-Type": "application/json",
        }
        try:
            async with self.session.post(
                self.bot_endpoint, json=payload, headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    logger.error(
                        f"DirectLine Agent received error status: {resp.status}"
                    )
                    return None
        except Exception as ex:
            logger.exception(
                f"Exception occurred while sending message to DirectLine Bot. {ex}"
            )
            return None

    async def close(self) -> None:
        """
        Clean up the aiohttp session.
        """
        await self.session.close()
