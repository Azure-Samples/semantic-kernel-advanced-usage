import sys
sys.path.append("../../")

from rich.console import Console
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import kernel_function

from src.models.events import SQLEvents
from src.models.step_models import (
    BusinessRulesStepInput, 
    ValidationStepInput, 
    SQLGenerationStepInput, 
    ValidationResult
)
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.utils.step_tracker import get_tracker
from src.constants.data_model import json_rules
from src.constants.prompts import business_rules_prompt

console = Console()
issue_history = []
# Track retry attempts to prevent infinite loops
br_retry_counter = 0
MAX_RETRIES = 3

class BusinessRulesStep(KernelProcessStep):

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

    @kernel_function(name="apply_business_rules")
    async def apply_business_rules(self, context: KernelProcessStepContext, data: BusinessRulesStepInput, kernel: Kernel):
        """Kernel function to apply business rules to SQL and emit the appropriate event."""
        global issue_history, br_retry_counter
        
        # Start tracking this step
        tracker = get_tracker()
        tracker.start_step("BusinessRulesStep", data)
        
        print("Running BusinessRulesStep...")
        print(f"Current business rules retry count: {br_retry_counter}")

        business_rules_result = await self._apply_business_rules(
            kernel=kernel,
            data=data
        )

        if business_rules_result.status == "OK" or br_retry_counter >= MAX_RETRIES:
            # Reset retry counter for future runs
            previous_retry_count = br_retry_counter
            br_retry_counter = 0
            
            # Business rules passed or max retries reached, proceed to validation
            result = ValidationStepInput(
                user_query=data.user_query,
                table_column_names=data.table_column_names,
                sql_statement=data.sql_generation_result.sql_statement
            )
            
            if previous_retry_count >= MAX_RETRIES:
                console.print("[yellow]Warning: Proceeding to validation despite business rule issues after maximum retries.[/yellow]")
                
            await context.emit_event(process_event=SQLEvents.BusinessRulesStepDone, data=result)
            print("Emitted event: BusinessRulesStepDone.")
            
            # End tracking with transition to ValidationStep
            tracker.end_step(next_step="ValidationStep", next_event=SQLEvents.BusinessRulesStepDone, output_data=result)
        else:
            # Business rules failed, but we'll retry only if under the max retry limit
            br_retry_counter += 1
            notes = f"Business rules validation failed (attempt {br_retry_counter}/{MAX_RETRIES}): {str(business_rules_result)}\nPrevious SQL Statement (need to improve):\n{data.sql_generation_result.sql_statement}"
            issue_history.append(notes)
            result = SQLGenerationStepInput(
                user_query=data.user_query, 
                table_column_names=data.table_column_names,
                notes="\n\n".join(issue_history)
            )
            await context.emit_event(process_event=SQLEvents.BusinessRulesFailed, data=result)
            print(f"Emitted event: BusinessRulesFailed. Retry {br_retry_counter}/{MAX_RETRIES}")
            
            # End tracking with transition back to SQLGenerationStep
            tracker.end_step(next_step="SQLGenerationStep", next_event=SQLEvents.BusinessRulesFailed, output_data=result)