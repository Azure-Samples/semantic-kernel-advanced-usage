import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from typing import Annotated
from semantic_kernel.contents.history_reducer.chat_history_reducer import (
    ChatHistoryReducer,
)
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
    agent_id: Annotated[
        str,
        "Agent ID selected by the orchestrator. Must be a valid agent_id from the list of available agents.",
    ]
    reason: Annotated[str, "Reasoning behind the agent_id selection."]


prompt = """
You are a team orchestrator that uses a chat history to determine the next best speaker in the conversation.

Your task is to return the agent_id of the speaker that is best suited to proceed based on the context provided in the chat history and the description of the agents, in JSON format as shown in the example output section
- You MUST return agent_id value from the list of available agents.
- The names are case-sensitive and should not be abbreviated or changed.
- DO REMEMBER chat history is sorted from oldest to newest. LATEST message is the last one in the list.
- DO NOT change the structure of the output, only the values.
- You MUST provide a reason for the agent_id selection.
- DO NOT output any additional formatting or text.
- When a user input is expected, you MUST select an agent capable of handling the user input.
- When provided, you can also take a decision based on tools available to each agent
- When provided, you can also take a decision based on the allowed transitions between agents.

### Example Output
{{"agent_id": "agent_1", "reason": "Agent 1 is the best speaker for the next turn."}}

### Agents

{agents}

### Chat History

{history}


BE SURE TO READ AGAIN THE INSTUCTIONS ABOVE BEFORE PROCEEDING.       
        """


class LastNMessagesHistoryReducer(ChatHistoryReducer):
    target_count: int = 3

    @override
    async def reduce(self) -> ChatHistoryReducer | None:
        # Filter out messages with role == AuthorRole.TOOL
        filtered_messages = [
            msg for msg in self.messages if msg.role != AuthorRole.TOOL
        ]
        if len(filtered_messages) <= self.target_count:
            self.messages = filtered_messages
            return None
        self.messages = filtered_messages[-self.target_count:]
        return self


class SpeakerElectionStrategy(SelectionStrategy):
    """
    An evolved version of the SelectionStrategy that uses agents descriptions
    and available tools (optiona) to determine the next best speaker in the conversation.
    """

    kernel: Kernel
    history_reducer: ChatHistoryReducer | None = LastNMessagesHistoryReducer()
    include_tools_descriptions: bool = (False,)
    allowed_transitions: dict["Agent", list["Agent"]] | None = None

    @override
    async def select_agent(
        self, agents: list["Agent"], history: list[ChatMessageContent]
    ) -> "Agent":

        # Reduce the history if needed
        # By default, we will use the last 3 messages to avoid overloading the model
        if self.history_reducer is not None:
            self.history_reducer.messages = history
            reduced_history = await self.history_reducer.reduce()
            if reduced_history is not None:
                history = reduced_history.messages

        # Flatten the history
        import json

        messages = [
            f"{idx+1}) {message.name or 'user'} => {json.dumps(message.content)}"
            for idx, message in enumerate(history)
            # For selection strategy, we only need messages from user and assistant
            if message.role in [AuthorRole.USER, AuthorRole.ASSISTANT]
            and message.content not in ["", None]
        ]

        agents_info = self._generate_agents_info(agents)

        execution_settings = {}
        # See https://devblogs.microsoft.com/semantic-kernel/using-json-schema-for-structured-output-in-python-for-openai-models/
        # We're using a custom format to make sure we get also the reason for the selection
        execution_settings["response_format"] = AgentChoiceResponse
        # Set temperature to 0 to ensure more deterministic results
        execution_settings["temperature"] = 0

        input_prompt = prompt.format(agents=agents_info, history="\n".join(messages))
        logger.info(f"SpeakerElectionStrategy input prompt: {input_prompt}")
        function = KernelFunctionFromPrompt(
            function_name="SpeakerElection", prompt=input_prompt
        )
        result = await function.invoke(
            kernel=self.kernel,
            execution_settings=execution_settings,
        )
        logger.info(f"SpeakerElectionStrategy: {result}")
        content = (
            # Strip markdown formatting if present
            result.value[0]
            .content.strip()
            .replace("```json", "")
            .replace("```", "")
        )
        parsed_result = AgentChoiceResponse.model_validate_json(content)

        # Add custom metadata to the current OpenTelemetry span
        span = trace.get_current_span()
        span.set_attribute("gen_ai.team.choice", parsed_result.agent_id)
        span.set_attribute("gen_ai.team.choice_reason", parsed_result.reason)

        return next(agent for agent in agents if agent.id == parsed_result.agent_id)

    def _generate_agents_info(self, agents: list["Agent"]) -> str:
        """
        Generate the agents info string to be used in the prompt. This includes
        the agent's ID and description, tools and allowed transitions if provided.

        :param agents: List of agents to be used in the prompt.

        :return: The agents info string.
        """
        agents_info = []
        for agent in agents:
            tools = []
            if self.include_tools_descriptions:
                for tool in agent.kernel.get_full_list_of_function_metadata():
                    tool_name = tool.name
                    tool_description = tool.description
                    tools.append(f"    - tool '{tool_name}': {tool_description}")
            tools_str = "\n".join(tools)

            transitions = []
            if self.allowed_transitions and agent in self.allowed_transitions:
                transitions = [
                    f"    - can transition to: {next_agent.id}"
                    for next_agent in self.allowed_transitions[agent]
                ]
            transitions_str = "\n".join(transitions)

            agent_info = f"- agent_id: {agent.id}\n    - description: {agent.description}\n{tools_str}\n{transitions_str}"
            agents_info.append(agent_info)

        return "\n".join(agents_info)
