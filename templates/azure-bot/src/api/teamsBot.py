from teams import Application, ApplicationOptions, TeamsAdapter
from teams.state import TurnState
from botbuilder.core import MemoryStorage, TurnContext
from semantic_kernel.contents import ChatHistory
from sk_conversation_agent import agent
from config import config

storage = MemoryStorage()

bot = Application[TurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=storage,
        # CANNOT PASS A DICT HERE; MUST PASS A CLASS WITH APP_ID, APP_PASSWORD, AND APP_TENANTID ATTRIBUTES
        adapter=TeamsAdapter(config),
    )
)


@bot.before_turn
async def setup_chathistory(context: TurnContext, state: TurnState):

    chat_history = state.conversation.get("chat_history") or ChatHistory()

    state.conversation["chat_history"] = chat_history

    return state


@bot.activity("message")
async def on_message(context: TurnContext, state: TurnState):
    user_message = context.activity.text

    # Get the chat_history from the conversation state
    chat_history: ChatHistory = state.conversation.get("chat_history")

    # Add the new user message
    chat_history.add_user_message(user_message)

    # Get the response from the semantic kernel agent (v1.22.0 and later)
    sk_response = await agent.get_response(
        history=chat_history, user_input=user_message
    )

    # Store the updated chat_history back into conversation state
    state.conversation["chat_history"] = chat_history

    # Send the response back to the user
    await context.send_activity(f"{sk_response}")

    return True
