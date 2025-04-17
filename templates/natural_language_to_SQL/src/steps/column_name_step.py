import sys
sys.path.append("../../")

import json
from rich.console import Console
from semantic_kernel.kernel import Kernel

from src.models.events import SQLEvents
from src.models.step_models import ColumnNamesStepInput, SQLGenerationStepInput, GetColumnNames
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.constants.data_model import json_rules, global_database_model
from src.constants.prompts import get_table_column_names_prompt_template
from src.steps.table_name_step import StepOutput

console = Console()

class ColumnNameStep:

    async def _get_column_names(self, kernel: Kernel, data: ColumnNamesStepInput) -> SQLGenerationStepInput:
        """Process the table names and extract relevant column names."""
        relevant_tables = []

        for table in data.table_names.table_names:
            for model_table in global_database_model:
                if table.table_name == model_table['TableName']:
                    relevant_tables.append(model_table)
                    break
        rules_with_query = json.dumps(json_rules, indent=4)
        
        prompt = get_table_column_names_prompt_template.format(
            user_query=data.user_query, 
            table_column_list=relevant_tables,
            previous_table_column_names=data.table_column_names,
            notes=data.notes,
            rules=rules_with_query
        )
        
        table_column_names = await call_chat_completion_structured_outputs(kernel, prompt, GetColumnNames)
        console.print(f"Extracted column names:\n", table_column_names)

        # Build model instance
        result = SQLGenerationStepInput(
            user_query=data.user_query, 
            table_column_names=table_column_names, 
            notes=data.notes
        )
        return result

    async def invoke(self, kernel: Kernel, data: ColumnNamesStepInput):
        """Process the step and return the output with an event ID."""
        print("Running ColumnNameStep...")

        result = await self._get_column_names(kernel=kernel, data=data)
        
        # Return a step output with event ID
        return StepOutput(id=SQLEvents.ColumnNameStepDone, data=result)