from semantic_kernel.agents import Agent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.agents.strategies.termination.termination_strategy import (
    TerminationStrategy,
)


class UserInputRequiredTerminationStrategy(TerminationStrategy):
    stop_agents: list["Agent"]

    async def should_agent_terminate(
        self, agent: "Agent", history: list["ChatMessageContent"]
    ) -> bool:
        return agent in self.stop_agents
