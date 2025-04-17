import sys
sys.path.append("../../")

import json
from rich.console import Console
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import kernel_function

from src.models.events import SQLEvents
from src.models.step_models import ColumnNamesStepInput, SQLGenerationStepInput, GetColumnNames
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.utils.step_tracker import get_tracker
from src.constants.data_model import json_rules, global_database_model
from src.constants.prompts import get_table_column_names_prompt_template

console = Console()

class ColumnNameStep(KernelProcessStep):

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

    @kernel_function(name="get_column_names")
    async def get_column_names(self, context: KernelProcessStepContext, data: ColumnNamesStepInput, kernel: Kernel):
        """Kernel function to extract column names based on the selected tables and emit the appropriate event."""
        tracker = get_tracker()
        tracker.start_step("ColumnNameStep", data)
        
        print("Running ColumnNameStep...")

        result = await self._get_column_names(kernel=kernel, data=data)
        
        await context.emit_event(process_event=SQLEvents.ColumnNameStepDone, data=result)
        print("Emitted event: ColumnNameStepDone.")
        
        tracker.end_step(next_step="SQLGenerationStep", next_event=SQLEvents.ColumnNameStepDone, output_data=result)