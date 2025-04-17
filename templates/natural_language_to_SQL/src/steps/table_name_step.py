import sys
sys.path.append("../../")

import json
from rich.console import Console
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import kernel_function

from src.models.events import SQLEvents
from src.models.step_models import TableNamesStepInput, ColumnNamesStepInput, GetTableNames
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.utils.step_tracker import get_tracker
from src.constants.data_model import json_rules, table_descriptions
from src.constants.prompts import get_table_names_prompt_template

console = Console()

class TableNameStep(KernelProcessStep):
    
    async def _get_table_names(self, kernel: Kernel, data: TableNamesStepInput) -> ColumnNamesStepInput:
        """Process the user query and extract relevant table names."""
        rules_with_query = json.dumps(json_rules, indent=4)
        
        prompt = get_table_names_prompt_template.format(
            user_query=data.user_query, 
            table_list=table_descriptions, 
            previous_table_column_names=data.table_column_names,
            notes=data.notes, 
            rules=rules_with_query
        )
        
        table_names = await call_chat_completion_structured_outputs(kernel, prompt, GetTableNames)
        console.print(f"Extracted table names:\n", table_names)

        # Build model instance
        result = ColumnNamesStepInput(
            user_query=data.user_query, 
            table_names=table_names, 
            notes=data.notes
        )
        return result

    @kernel_function(name="get_table_names")
    async def get_table_names(self, context: KernelProcessStepContext, data: TableNamesStepInput, kernel: Kernel):
        """Kernel function to extract table names from user query and emit the appropriate event."""
        tracker = get_tracker()
        # Using the async version of start_step
        await tracker.start_step_async("TableNameStep", data)
        
        print("Running TableNameStep...")
        print(f"Received user query: {data.user_query}")
        result = await self._get_table_names(kernel=kernel, data=data)

        await context.emit_event(process_event=SQLEvents.TableNameStepDone, data=result)
        print("Emitted event: TableNameStepDone.")
        
        # Using the async version of end_step
        await tracker.end_step_async(next_step="ColumnNameStep", next_event=SQLEvents.TableNameStepDone, output_data=result)