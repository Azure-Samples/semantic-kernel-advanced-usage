from dotenv import load_dotenv

load_dotenv(override=True)

import chainlit as cl

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from context_reducer import ContextAwareChatHistoryReducer
from telco.telco_team import telco_team
from semantic_kernel.agents import Agent

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure logging level is set as required


class IgnoreTranslationMessageFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "Translation file for it not found" not in record.getMessage()


# Add the filter to the chainlit logger (or whichever logger emits the message)
logging.getLogger("chainlit").addFilter(IgnoreTranslationMessageFilter())

agent: Agent = telco_team


@cl.on_message
async def on_message(message: cl.Message):
    """
    This function is called when a message is received from the user.
    """
    history: ContextAwareChatHistoryReducer = cl.user_session.get(
        "history",
        ContextAwareChatHistoryReducer(messages=[], target_count=100, auto_reduce=True),
    )
    # Calling the add_message_async method to add the user message to the history
    # and with auto_reduce=True, the history will be reduced => context message will be created
    await history.add_message_async(
        ChatMessageContent(content=message.content, role=AuthorRole.USER, name="user")
    )

    async for result in agent.invoke(history=history):
        content = result.content
        if "PAUSE" not in content:
            if "~~~context~~~" in content:
                content = content.split("~~~context~~~")[0]
            await cl.Message(content=content, author=result.name).send()

    cl.user_session.set("history", history)
