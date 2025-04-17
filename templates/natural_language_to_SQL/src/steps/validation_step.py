import sys
sys.path.append("../../")

from rich.console import Console
from semantic_kernel.kernel import Kernel

from src.models.events import SQLEvents
from src.models.step_models import (
    ValidationStepInput,
    ExecutionStepInput,
    SQLGenerationStepInput,
    ValidationResult
)
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.constants.data_model import global_database_model
from src.constants.prompts import sql_validation_prompt
from src.steps.table_name_step import StepOutput

console = Console()
issue_history = []

class ValidationStep:

    async def _validate_sql(self, kernel: Kernel, user_query: str, data: ValidationStepInput) -> ValidationResult:
        """Validate the SQL statement against database schema and query standards."""
        relevant_tables = []
        for table in data.table_column_names.table_column_list:
            for model_table in global_database_model:
                if table.table_name == model_table['TableName']:
                    relevant_tables.append(model_table)
                    break
                    
        prompt = sql_validation_prompt.format(
            question=user_query, 
            sql_query=data.sql_statement, 
            table_column_names=relevant_tables
        )
        validation_result = await call_chat_completion_structured_outputs(kernel, prompt, ValidationResult)
        console.print(f"SQL validation results:\n", validation_result)
        return validation_result

    async def invoke(self, kernel: Kernel, data: ValidationStepInput):
        """Process the step and return the output with an event ID."""
        global issue_history
        print("Running ValidationStep...")
        print(f"SQL statement to validate: {data.sql_statement}")        
        validation_result = await self._validate_sql(kernel=kernel, user_query=data.user_query, data=data)
        
        # Check if we have fixes from validation that we can use
        if validation_result.list_of_fixes and len(validation_result.list_of_fixes) > 0:
            # Extract the SQL from the list_of_fixes if it contains SQL statements
            fixed_sql = None
            for fix in validation_result.list_of_fixes:
                # Look for SQL statement in the fix suggestions
                if "SELECT" in fix and (
                    "FROM" in fix or 
                    "JOIN" in fix or 
                    "WHERE" in fix or 
                    "GROUP BY" in fix or 
                    "ORDER BY" in fix
                ):
                    fixed_sql = fix
                    break
            
            if fixed_sql:
                print(f"Using fixed SQL from validation: {fixed_sql}")
                # Use the fixed SQL directly for execution
                result = ExecutionStepInput(
                    user_query=data.user_query,
                    table_column_names=data.table_column_names,
                    sql_statement=fixed_sql
                )
                return StepOutput(id=SQLEvents.ValidationPassed, data=result)
                
        if validation_result.status == "OK":
            # Validation passed, proceed to execution with original SQL
            result = ExecutionStepInput(
                user_query=data.user_query,
                table_column_names=data.table_column_names,
                sql_statement=data.sql_statement
            )
            return StepOutput(id=SQLEvents.ValidationPassed, data=result)
        else:
            # Validation failed, check if we need to regenerate SQL
            if validation_result.list_of_fixes:
                # We have suggestions but no complete SQL, so regenerate SQL with these suggestions
                detailed_notes = []
                if isinstance(validation_result.list_of_issues, list) and validation_result.list_of_issues:
                    detailed_notes.append("Issues identified:")
                    for i, issue in enumerate(validation_result.list_of_issues):
                        detailed_notes.append(f"  {i+1}. {issue}")
                
                if isinstance(validation_result.list_of_fixes, list) and validation_result.list_of_fixes:
                    detailed_notes.append("Suggested fixes:")
                    for i, fix in enumerate(validation_result.list_of_fixes):
                        detailed_notes.append(f"  {i+1}. {fix}")
                
                notes = f"Validation failed. Previous SQL Statement (need to improve):\n{data.sql_statement}\n\n" + "\n".join(detailed_notes)
                issue_history.append(notes)
                
                print(f"Regenerating SQL with validation suggestions:\n{notes}")
                
                # Return to SQL generation with detailed notes
                result = SQLGenerationStepInput(
                    user_query=data.user_query, 
                    table_column_names=data.table_column_names,
                    notes="\n\n".join(issue_history)
                )
                return StepOutput(id=SQLEvents.ValidationFailed, data=result)
            else:
                # No specific fixes given, just regenerate with original notes
                notes = f"Validation failed: {str(validation_result)}\nPrevious SQL Statement (need to improve):\n{data.sql_statement}"
                issue_history.append(notes)
                result = SQLGenerationStepInput(
                    user_query=data.user_query, 
                    table_column_names=data.table_column_names,
                    notes="\n\n".join(issue_history)
                )
                return StepOutput(id=SQLEvents.ValidationFailed, data=result)