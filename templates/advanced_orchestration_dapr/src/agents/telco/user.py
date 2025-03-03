from semantic_kernel.agents import ChatCompletionAgent
from sk_ext.basic_kernel import create_service

user_agent = ChatCompletionAgent(
    id="user_agent",
    name="User",
    service=create_service(),
    description="A human user that interacts with the system. Can provide input to the chat",
    instructions="Always respond PAUSE",
)
