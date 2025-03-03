import sys
sys.path.append("../../")

from rich.console import Console
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import kernel_function

from src.models.events import SQLEvents
from src.models.step_models import ExecutionStepInput, Execution2TableNames
from src.utils.db_helpers import SQLite_exec_sql

console = Console()

class ExecutionStep(KernelProcessStep):
    """Execute SQL statement and emit appropriate event."""
    @kernel_function(name="execute_sql")
    async def execute_sql(self, context: KernelProcessStepContext, data: ExecutionStepInput, kernel: Kernel):
        print("Running ExecutionStep...")
        print(f"SQL statement to execute: {data.sql_statement}")

        try:
            response = SQLite_exec_sql(data.sql_statement)
            console.print(response)
            print("SQL execution succeeded.")
            await context.emit_event(process_event=SQLEvents.ExecutionSuccess, data=data.sql_statement)
            print("Emitted event: ExecutionSuccess.")
        except Exception as e:
            error_description = f"Execution error: {str(e)}"
            result = Execution2TableNames(
                user_query=data.user_query,
                table_names=data.table_names,
                column_names=data.column_names,
                sql_statement=data.sql_statement,
                error_description=error_description
            )
            await context.emit_event(process_event=SQLEvents.ExecutionError, data=result)
            print("Emitted event: ExecutionError.")