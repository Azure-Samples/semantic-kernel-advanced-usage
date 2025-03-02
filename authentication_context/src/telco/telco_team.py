from telco.sales import sales_agent
from telco.technical import technical_agent
from telco.user import user_agent
from telco.billing import billing_agent
from telco.auth import auth_agent

from sk_ext.speaker_election_strategy import (
    SpeakerElectionStrategy,
    LastNMessagesHistoryReducer,
)
from sk_ext.termination_strategy import UserInputRequiredTerminationStrategy
from sk_ext.basic_kernel import create_kernel
from sk_ext.team import Team

kernel = create_kernel()

telco_team = Team(
    id="customer-support",
    name="customer-support",
    description="Customer support team",
    agents=[user_agent, sales_agent, technical_agent, billing_agent, auth_agent],
    # We opt to extend the last 10 messages to determine the speaker,
    # to allow conversation to resume after authentication
    selection_strategy=SpeakerElectionStrategy(
        kernel=kernel, history_reducer=LastNMessagesHistoryReducer(n=6)
    ),
    termination_strategy=UserInputRequiredTerminationStrategy(stop_agents=[user_agent]),
)
