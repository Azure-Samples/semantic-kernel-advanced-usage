import chainlit as cl
from dotenv import load_dotenv
import os
import logging
from copilot_studio_agent import CopilotAgent
from directline_client import DirectLineClient
from copilot_studio_agent_thread import CopilotAgentThread

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logging.getLogger("copilot_studio_agent").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


client = DirectLineClient(
    copilot_agent_secret=os.getenv("BOT_SECRET"),
    directline_endpoint="https://europe.directline.botframework.com/v3/directline"
)

agent = CopilotAgent(
    id="copilot_studio",
    name="copilot_studio",
    description="copilot_studio",
    directline_client=client,
)


@cl.on_chat_start
async def on_chat_start():
    thread = CopilotAgentThread(
        directline_client=client,
    )
    cl.user_session.set("thread", thread)


@cl.on_message
async def on_message(message: cl.Message):
    thread: CopilotAgentThread = cl.user_session.get("thread")

    response = await agent.get_response(messages=message.content, thread=thread)

    cl.user_session.set("thread", thread)

    logger.info(f"Response: {response}")

    await cl.Message(content=response.message.content, author=agent.name).send()
