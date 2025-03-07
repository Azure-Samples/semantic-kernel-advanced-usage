import chainlit as cl
from dotenv import load_dotenv
import os
from direct_line_agent import DirectLineAgent
from semantic_kernel.contents.chat_history import ChatHistory

load_dotenv(override=True)

agent = DirectLineAgent(
    id="copilot_studio",
    name="copilot_studio",
    description="copilot_studio",
    bot_secret=os.getenv("BOT_SECRET"),
    bot_endpoint="https://europe.directline.botframework.com/v3/directline",
)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("chat_history", ChatHistory())


@cl.on_message
async def on_message(message: cl.Message):
    chat_history: ChatHistory = cl.user_session.get("chat_history")

    chat_history.add_user_message(message.content)

    response = await agent.get_response(history=chat_history)

    cl.user_session.set("chat_history", chat_history)

    await cl.Message(content=response, author="copilot_studio").send()
