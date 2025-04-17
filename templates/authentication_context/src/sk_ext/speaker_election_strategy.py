import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.kernel import Kernel
from semantic_kernel.agents import Agent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.agents.strategies.selection.selection_strategy import (
    SelectionStrategy,
)
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)


class AgentChoiceResponse(KernelBaseModel):
    agent_id: str
    reasoning: str


prompt = """
You are a team orchestrator that uses a chat history to determine the next best speaker in the conversation.

You have the following agents to choose from:
{{$agents}}

Below is an example of how to specify your response:
Agent ID: <agent_id>
Reasoning: <reasoning>

For the current conversation history:
{{$chat_history}}

Which agent should respond next? Explain your choice.
"""


class SpeakerElectionStrategy(SelectionStrategy):
    """
    Strategy that uses a prompted LLM to select the next agent to speak,
    based on their description and the context of the conversation.

    Args:
        excluded_agents (list, optional): list of agents to exclude from selection. Defaults to None.
    """

    def __init__(self, excluded_agents: list = None):
        self._excluded_agents = excluded_agents or []

    @override
    async def select_agent(
        self,
        agents: list[Agent],
        chat_history: list[ChatMessageContent],
        kernel: Kernel,
        arguments: KernelArguments = None,
    ) -> Agent:
        """Select the next agent to respond based on the chat history."""
        if arguments is None:
            arguments = KernelArguments()

        # If there's only one agent, select it
        available_agents = [
            agent for agent in agents if agent.id not in self._excluded_agents
        ]
        if len(available_agents) == 1:
            logger.info(f"Only one agent available: {available_agents[0].id}")
            return available_agents[0]

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("select_agent") as span:
            # Create a prompt with agent descriptions and the chat history
            agents_descriptions = []
            for agent in available_agents:
                agents_descriptions.append(f"ID: {agent.id}")
                agents_descriptions.append(f"Name: {agent.name}")
                if agent.description:
                    agents_descriptions.append(f"Description: {agent.description}")
                agents_descriptions.append("---")
            agents_descriptions_str = "\n".join(agents_descriptions)

            # Create a readable chat history
            chat_history_lines = []
            for message in chat_history:
                role = message.role
                if message.role == AuthorRole.ASSISTANT:
                    # If the message is from an assistant, use the metadata to get the agent ID
                    if hasattr(message, "ai_model_id") and message.ai_model_id:
                        role = f"ASSISTANT ({message.ai_model_id})"
                    elif hasattr(message, "metadata") and message.metadata.get("agent_id"):
                        role = f"ASSISTANT ({message.metadata.get('agent_id')})"
                chat_history_lines.append(f"{role}: {message.content}")
            chat_history_str = "\n".join(chat_history_lines)

            # Add the chat history and agent descriptions to the arguments
            arguments["agents"] = agents_descriptions_str
            arguments["chat_history"] = chat_history_str

            # Create a function that uses a kernel to generate a response
            func = KernelFunctionFromPrompt(
                prompt=prompt,
                template_format="handlebars",
                description="Selects the next agent to respond based on the chat history",
                name="select_agent",
                response_type=AgentChoiceResponse,
            )

            # Use the kernel to predict which agent should respond
            result = await kernel.invoke(
                func,
                arguments=arguments,
            )

            # Find the agent by ID
            selected_agent_id = result.agent_id
            selected_agent = None
            for agent in available_agents:
                if agent.id == selected_agent_id:
                    selected_agent = agent
                    break

            # If no agent found with the predicted ID, log a warning and select the first one
            if selected_agent is None:
                logger.warning(
                    f"No agent found with ID {selected_agent_id}. Using first available agent."
                )
                selected_agent = available_agents[0]

            # Log the selection
            logger.info(
                f"Selected agent: {selected_agent.id} ({selected_agent.name}). Reasoning: {result.reasoning}"
            )
            
            # Add spans for better observability
            span.set_attribute("selected_agent_id", selected_agent.id)
            span.set_attribute("selected_agent_name", selected_agent.name)
            span.set_attribute("selection_reasoning", result.reasoning)
            
            return selected_agent
