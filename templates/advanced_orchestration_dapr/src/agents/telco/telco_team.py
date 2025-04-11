from telco.sales import sales_agent
from telco.technical import technical_agent
from telco.user import user_agent
from telco.billing import billing_agent

from sk_ext.speaker_election_strategy import SpeakerElectionStrategy
from sk_ext.termination_strategy import UserInputRequiredTerminationStrategy
from sk_ext.basic_kernel import create_kernel
from sk_ext.team import Team
from sk_ext.planning_strategy import DefaultPlanningStrategy
from sk_ext.feedback_strategy import DefaultFeedbackStrategy
from sk_ext.merge_strategy import KernelFunctionMergeHistoryStrategy
from sk_ext.planned_team import PlannedTeam

from semantic_kernel.functions.kernel_function_from_prompt import (
    KernelFunctionFromPrompt,
)

kernel = create_kernel()

planned_team = PlannedTeam(
    id="planned-team",
    name="planned-team",
    description="A special agent that can handle more complex asks by orchestrating multiple agents. Useful when user asks spans multiple domains.",
    agents=[sales_agent, technical_agent, billing_agent],
    planning_strategy=DefaultPlanningStrategy(
        kernel=kernel, include_tools_descriptions=True
    ),
    feedback_strategy=DefaultFeedbackStrategy(kernel=kernel),
    fork_history=True,
    merge_strategy=KernelFunctionMergeHistoryStrategy(
        kernel=kernel,
        kernel_function=KernelFunctionFromPrompt(
            function_name="merge_history",
            prompt="""Summarize the following message to provide a single consolidated response.
Output must in plain text or markdown format.

# MESSAGES
{{{{$messages}}}}
""",
        ),
    ),
)
telco_team = Team(
    id="customer-support",
    name="customer-support",
    description="Customer support team",
    agents=[user_agent, sales_agent, technical_agent, billing_agent, planned_team],
    selection_strategy=SpeakerElectionStrategy(kernel=kernel),
    termination_strategy=UserInputRequiredTerminationStrategy(stop_agents=[user_agent]),
)
