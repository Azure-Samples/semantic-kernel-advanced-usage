import asyncio
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
    Instead of directly supplying a secret and conversation ID, the agent queries a token_endpoint
    to retrieve the token and then starts a conversation.
    """

    token_endpoint: str
    bot_endpoint: str
    conversation_id: str | None = None
    directline_token: str | None = None
    session: aiohttp.ClientSession = aiohttp.ClientSession()

    async def _fetch_token_and_conversation(self) -> None:
        """
        Query the token_endpoint to retrieve the DirectLine token.
        Expects a JSON response with a 'token' key.
        """
        try:
            async with self.session.get(self.token_endpoint) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.directline_token = data.get("token")
                    if not self.directline_token:
                        logger.error("Token endpoint returned no token: %s", data)
                        raise AgentInvokeException("No token received.")
                else:
                    logger.error("Token endpoint error status: %s", resp.status)
                    raise AgentInvokeException(
                        "Failed to fetch token from token endpoint."
                    )
        except Exception as ex:
            logger.exception("Exception fetching token: %s", ex)
            raise AgentInvokeException(
                "Exception occurred while fetching token."
            ) from ex

    async def get_response(
        self,
        history: ChatHistory,
        arguments: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ChatMessageContent:
        """
        Get a response from the DirectLine Bot.
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
        Send the latest message from the chat history to the DirectLine Bot
        and yield responses. This sends the payload after ensuring that:
          1. The token is fetched.
          2. A conversation is started.
          3. The activity payload is posted.
          4. Activities are polled until an event "DynamicPlanFinished" is received.
        """
        payload = self._build_payload(history, arguments, **kwargs)
        response_data = await self._send_message(payload)
        if response_data is None or "activities" not in response_data:
            raise AgentInvokeException(
                f"Invalid response from DirectLine Bot.\n{response_data}"
            )

        logger.debug("DirectLine Bot response: %s", response_data)

        for activity in response_data["activities"]:
            message = ChatMessageContent(
                role=activity.get("from", {}).get("role", "assistant"),
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
        Uses the latest message from the chat history.
        """
        latest_message = history.messages[-1] if history.messages else None
        text = latest_message.content if latest_message else "Hello"
        payload = {
            "type": "message",
            "from": {"id": "user"},
            "text": text,
        }
        # Optionally include conversationId if available.
        if self.conversation_id:
            payload["conversationId"] = self.conversation_id
        return payload

    async def _send_message(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        1. Ensure the token is fetched.
        2. Start a conversation by posting to the bot_endpoint /conversations endpoint (without a payload)
        3. Post the payload to /conversations/{conversationId}/activities
        4. Poll GET /conversations/{conversationId}/activities every 1s until an activity
           with type="event" and name="DynamicPlanFinished" is found.
        """
        if not self.directline_token:
            await self._fetch_token_and_conversation()

        headers = {
            "Authorization": f"Bearer {self.directline_token}",
            "Content-Type": "application/json",
        }

        # Step 2: Start a conversation if one hasn't already been started.
        if not self.conversation_id:
            start_conv_url = f"{self.bot_endpoint}/conversations"
            async with self.session.post(start_conv_url, headers=headers) as resp:
                if resp.status not in (200, 201):
                    logger.error(
                        "Failed to start conversation. Status: %s", resp.status
                    )
                    raise AgentInvokeException("Failed to start conversation.")
                conv_data = await resp.json()
                self.conversation_id = conv_data.get("conversationId")
                if not self.conversation_id:
                    raise AgentInvokeException(
                        "Conversation ID not found in start response."
                    )

        # Step 3: Post the message payload.
        activities_url = (
            f"{self.bot_endpoint}/conversations/{self.conversation_id}/activities"
        )
        async with self.session.post(
            activities_url, json=payload, headers=headers
        ) as resp:
            if resp.status != 200:
                logger.error("Failed to post activity. Status: %s", resp.status)
                raise AgentInvokeException("Failed to post activity.")
            _ = await resp.json()  # Response from posting activity is ignored.

        # Step 4: Poll for activities until DynamicPlanFinished event is found.
        finished = False
        collected_data = None
        while not finished:
            async with self.session.get(activities_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    activities = data.get("activities", [])
                    if any(
                        activity.get("type") == "event"
                        and activity.get("name") == "DynamicPlanFinished"
                        for activity in activities
                    ):
                        collected_data = data
                        finished = True
                        break
                else:
                    logger.error("Error polling activities. Status: %s", resp.status)
            await asyncio.sleep(1)

        return collected_data

    async def close(self) -> None:
        """
        Clean up the aiohttp session.
        """
        await self.session.close()

    async def invoke_stream(self, *args, **kwargs):
        return super().invoke_stream(*args, **kwargs)
