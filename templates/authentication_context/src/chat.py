import chainlit as cl
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatHistoryAgentThread
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
    thread: ChatHistoryAgentThread = cl.user_session.get("thread")
    if not thread:
        thread = ChatHistoryAgentThread(
            thread_id=cl.user_session.get("id"),
            chat_history=ContextAwareChatHistoryReducer(messages=[], target_count=100, auto_reduce=True)
        )

    await thread.reduce()
    async for result in agent.invoke(messages=message.content, thread=thread):
        message = result.message
        content = message.content
        if "PAUSE" not in content:
            if "~~~context~~~" in content:
                content = content.split("~~~context~~~")[0]
            await cl.Message(content=content, author=result.name).send()

    cl.user_session.set("thread", thread)
