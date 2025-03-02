from abc import ABC
from typing import TYPE_CHECKING, Annotated

from semantic_kernel.agents import Agent
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents.history_reducer.chat_history_reducer import (
    ChatHistoryReducer,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_from_prompt import (
    KernelFunctionFromPrompt,
)
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)


class TeamPlanStep(KernelBaseModel):
    agent_id: Annotated[str, "The agent_id of the agent to execute"]
    instructions: Annotated[str, "The instructions for the agent"]


class TeamPlan(KernelBaseModel):
    plan: Annotated[list[TeamPlanStep], "The plan to be executed by the team"]


class PlanningStrategy(KernelBaseModel, ABC):
    """Base strategy class for creating a plan to solve the user inquiry by using the available agents."""

    history_reducer: ChatHistoryReducer | None = None
    include_tools_descriptions: bool = False

    async def create_plan(
        self,
        agents: list[Agent],
        history: list["ChatMessageContent"],
        feedback: str = "",
    ) -> TeamPlan:
        """ """
        raise AgentExecutionException("create_plan not implemented")


class DefaultPlanningStrategy(PlanningStrategy):
    """
    Default planning strategy that uses a kernel function to create a plan to solve the user inquiry by using the available agents.
    """

    kernel: Kernel

    async def create_plan(
        self,
        agents: list[Agent],
        history: list["ChatMessageContent"],
        feedback: str = "",
    ) -> TeamPlan:
        prompt = """
You are a team orchestrator that must create a plan to solve the user inquiry by using the available agents.
Your task is to create a plan that includes only the agents suitable to help, based on their descriptions.
The plan must be a list of agent_id values, in the order they should be executed, along with the proper instructions for each agent.
When FEEDBACK section has content, you must consider it to tailor the plan accordingly, since this means a previous plan was not successful to meet success criteria.
The plan must be returned as JSON, with the following structure:

{{
    "plan": [
        {{
            "agent_id": "agent_id",
            "instructions": "instructions"
        }},
        ...
    ]
}}

You MUST return the plan in the format specified above. DO NOT return anything else.

# AVAILABLE AGENTS
{agents}

# INQUIRY
{inquiry}

# FEEDBACK
{feedback}

BE SURE TO READ AGAIN THE INSTUCTIONS ABOVE BEFORE PROCEEDING.
"""
        if self.history_reducer is not None:
            self.history_reducer.messages = history
            reduced_history = await self.history_reducer.reduce()
            if reduced_history is not None:
                history = reduced_history.messages

        # Flatten the history
        messages = [
            {
                "role": str(message.role),
                "content": message.content,
                "name": message.name or "user",
            }
            for message in history
        ]

        agents_info = self._generate_agents_info(agents)

        # Invoke the function
        arguments = KernelArguments()

        execution_settings = {}
        # https://devblogs.microsoft.com/semantic-kernel/using-json-schema-for-structured-output-in-python-for-openai-models/
        execution_settings["response_format"] = TeamPlan

        input_prompt = prompt.format(
            agents=agents_info, inquiry=messages[-1]["content"], feedback=feedback
        )
        logger.info(f"CreatePlan prompt: {input_prompt}")
        kfunc = KernelFunctionFromPrompt(
            function_name="CreatePlan", prompt=input_prompt
        )
        result = await kfunc.invoke(
            kernel=self.kernel,
            arguments=arguments,
            execution_settings=execution_settings,
        )
        logger.info(f"CreatePlan: {result}")
        content = (
            result.value[0].content.strip().replace("```json", "").replace("```", "")
        )
        parsed_result = TeamPlan.model_validate_json(content)

        # Add custom metadata to the current OpenTelemetry span
        span = trace.get_current_span()
        span.set_attribute("gen_ai.plannedteam.plan", parsed_result.model_dump_json())

        return parsed_result

    def _generate_agents_info(self, agents: list["Agent"]) -> str:
        agents_info = []
        for agent in agents:
            tools = []
            if self.include_tools_descriptions:
                agent_tools = agent.kernel.get_full_list_of_function_metadata()
                for tool in agent_tools:
                    tool_name = tool.name
                    tool_description = tool.description
                    tools.append(f"    - tool '{tool_name}': {tool_description or ''}")
            tools_str = "\n".join(tools)

            agent_info = f"- agent_id: {agent.id}\n    - description: {agent.description}\n{tools_str}\n\n"
            agents_info.append(agent_info)

        return "\n".join(agents_info)
