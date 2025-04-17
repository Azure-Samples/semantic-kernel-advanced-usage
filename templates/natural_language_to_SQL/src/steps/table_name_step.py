import sys
sys.path.append("../../")

import json
from rich.console import Console
from dataclasses import dataclass
from semantic_kernel.kernel import Kernel

from src.models.events import SQLEvents
from src.models.step_models import TableNamesStepInput, ColumnNamesStepInput, GetTableNames
from src.utils.chat_helpers import call_chat_completion_structured_outputs
from src.constants.data_model import json_rules, table_descriptions
from src.constants.prompts import get_table_names_prompt_template

console = Console()

@dataclass
class StepOutput:
    id: str  # Event ID
    data: any  # Output data

class TableNameStep:
    
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

    async def invoke(self, kernel: Kernel, data: TableNamesStepInput):
        """Process the step and return the output with an event ID."""
        print("Running TableNameStep...")
        print(f"Received user query: {data.user_query}")
        result = await self._get_table_names(kernel=kernel, data=data)

        # Return a step output with event ID
        return StepOutput(id=SQLEvents.TableNameStepDone, data=result)