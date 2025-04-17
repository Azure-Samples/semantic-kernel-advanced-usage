import sys
sys.path.append("../../")

from rich.console import Console
from semantic_kernel.kernel import Kernel

from src.models.events import SQLEvents
from src.models.step_models import (
    BusinessRulesStepInput, 
    ValidationStepInput, 
    SQLGenerationStepInput, 
    ValidationResult
)
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.constants.data_model import json_rules
from src.constants.prompts import business_rules_prompt
from src.steps.table_name_step import StepOutput

console = Console()
issue_history = []

class BusinessRulesStep:

    async def _apply_business_rules(self, kernel: Kernel, data: BusinessRulesStepInput) -> ValidationResult:
        """Apply business rules to the generated SQL statement."""
        rules_with_query = json_rules.format(question=data.user_query)
        
        prompt = business_rules_prompt.format(
            question=data.user_query,
            rules=rules_with_query,
            sql_query=data.sql_generation_result.sql_statement
        )
        business_rules_result = await call_chat_completion_structured_outputs(kernel, prompt, ValidationResult)
        console.print(f"Applied business rules:\n", business_rules_result)
        return business_rules_result

    async def invoke(self, kernel: Kernel, data: BusinessRulesStepInput):
        """Process the step and return the output with an event ID."""
        global issue_history
        print("Running BusinessRulesStep...")

        business_rules_result = await self._apply_business_rules(
            kernel=kernel,
            data=data
        )

        if business_rules_result.status == "OK":
            # Business rules passed, proceed to validation
            result = ValidationStepInput(
                user_query=data.user_query,
                table_column_names=data.table_column_names,
                sql_statement=data.sql_generation_result.sql_statement
            )
            return StepOutput(id=SQLEvents.BusinessRulesStepDone, data=result)
        else:
            # Business rules failed, return to SQL generation with notes
            notes = f"Validation failed: {str(business_rules_result)}\nPrevious SQL Statement (need to improve):\n{data.sql_generation_result.sql_statement}"
            issue_history.append(notes)
            result = SQLGenerationStepInput(
                user_query=data.user_query, 
                table_column_names=data.table_column_names,
                notes="\n\n".join(issue_history)
            )
            return StepOutput(id=SQLEvents.BusinessRulesFailed, data=result)