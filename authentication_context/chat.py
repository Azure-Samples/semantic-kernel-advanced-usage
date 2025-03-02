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
        await cl.Message(content=result.content, author=result.name).send()

    cl.user_session["history"] = history
