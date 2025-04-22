from semantic_kernel.contents.chat_message_content import ChatMessageContent
from dapr.actor import ActorInterface, actormethod, ActorProxyFactory, ActorId
import logging
import chainlit as cl
from dotenv import load_dotenv

load_dotenv(override=True)


class SKAgentActorInterface(ActorInterface):
    @actormethod(name="invoke")
    async def invoke(self, input_message: str) -> list[dict]: ...

    @actormethod(name="get_history")
    async def get_history(self) -> dict: ...


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure logging level is set as required


@cl.on_message
async def on_message(message: cl.Message):
    """
    This function is called when a message is received from the user.
    """
    # We assume the Chainlit session ID can be used
    # as the "conversation ID"
    session_id = cl.user_session.get("id")

    # Create an actor proxy to the SKAgentActor
    # Thanks to Dapr, no need to worry about the
    # actor's location or how to communicate with it
    proxy: SKAgentActorInterface = ActorProxyFactory(http_timeout_seconds=120).create(
        actor_type="SKAgentActor",  # This is the actor type name
        actor_id=ActorId(session_id),
        actor_interface=SKAgentActorInterface,  # This is the actor interface, must match the one in the actor
    )

    # Invoke the actor with the user's message
    results = await proxy.invoke(message.content)
    for result in results:
        # Deserialize the result from the actor generic "dict" type
        response = ChatMessageContent.model_validate(result)
        logger.debug(f"Received result from agent: {result}")
        # NOTE: "content" is a field in the ChatMessageContent model, BUT not in the dict!
        await cl.Message(content=response.content, author=response.name).send()
