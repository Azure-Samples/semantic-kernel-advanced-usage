import sys
sys.path.append("../../")

import os
from rich.console import Console
from semantic_kernel.kernel import Kernel

from src.models.events import SQLEvents
from src.models.step_models import SQLGenerationStepInput, BusinessRulesStepInput, TableNamesStepInput, SQLGenerateResult
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.utils.db_helpers import write_to_file
from src.constants.data_model import json_rules, global_database_model
from src.constants.prompts import sql_generation_prompt, few_shot_examples
from src.steps.table_name_step import StepOutput

console = Console()

# Global counter for prompt output files
counter = 0
# Track issues for retries
issue_history = []

class SQLGenerationStep:

    async def _generate_sql(self, kernel: Kernel, user_query: str, data: SQLGenerationStepInput) -> SQLGenerateResult:
        """Generate SQL statement using LLM based on user query and selected tables/columns."""
        global counter

        relevant_tables = []

        for table in data.table_column_names.table_column_list:
            for model_table in global_database_model:
                if table.table_name == model_table['TableName']:
                    relevant_columns = []
                    for column in table.column_names:
                        for model_column in model_table['Columns']:
                            if column == model_column['ColumnName']:
                                relevant_columns.append(model_column)
                    relevant_tables.append({
                        'TableName': model_table['TableName'],
                        'Description': model_table['Description'],
                        'Columns': relevant_columns
                        }
                    )

        rules_with_query = json_rules.format(question=user_query)
        
        prompt = sql_generation_prompt.format(
            suggested_table_column_names=data.table_column_names,
            data_model=relevant_tables,
            rules=rules_with_query,
            question=user_query,
            examples=few_shot_examples,
            notes=data.notes
        )

        # Save prompt for debugging
        os.makedirs("output_prompts", exist_ok=True)
        write_to_file(prompt, f"output_prompts/prompt_{counter}.txt", "w")
        counter += 1

        sql_generation_result = await call_chat_completion_structured_outputs(kernel, prompt, SQLGenerateResult)
        console.print(f"Generated SQL statement:\n", sql_generation_result)

        return sql_generation_result

    async def invoke(self, kernel: Kernel, data: SQLGenerationStepInput):
        """Process the step and return the output with an event ID."""
        global issue_history
        print("Running SQLGenerationStep...")

        sql_generation_result = await self._generate_sql(kernel=kernel, user_query=data.user_query, data=data)

        if sql_generation_result.status == "IMPOSSIBLE":
            # Build model instance for retrying with better table selection
            notes = f"SQL Generation failed: {str(sql_generation_result.reason)}\nPrevious SQL Statement (need to improve):\n{sql_generation_result.sql_statement}"
            issue_history.append(notes)
            result = TableNamesStepInput(
                user_query=data.user_query, 
                table_column_names=data.table_column_names,
                notes="\n\n".join(issue_history)
            )
            return StepOutput(id=SQLEvents.SQLGenerationStepFailed, data=result)
        else: 
            # Build model instance for business rules validation
            result = BusinessRulesStepInput(
                user_query=data.user_query, 
                table_column_names=data.table_column_names, 
                sql_generation_result=sql_generation_result
            )
            return StepOutput(id=SQLEvents.SQLGenerationStepDone, data=result)