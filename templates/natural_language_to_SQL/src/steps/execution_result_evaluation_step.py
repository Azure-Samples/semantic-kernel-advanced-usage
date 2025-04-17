import sys
sys.path.append("../../")

from rich.console import Console
# Comment out or remove process imports as they're not used in the main workflow
# The main SQL process doesn't use this file, it uses execution_step.py instead
# from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.kernel import Kernel
# from semantic_kernel.functions import kernel_function

from src.models.events import SQLEvents
from src.models.step_models import ExecutionStepInput, Execution2TableNames
from src.utils.db_helpers import SQLite_exec_sql

console = Console()

# Modify the class to not inherit from KernelProcessStep since we're not using processes
class ExecutionResultEvaluationStep:
    """Execute SQL statement and emit appropriate event."""
    # @kernel_function(name="execute_sql")
    async def evaluate_execution_result(self, kernel: Kernel, data: ExecutionStepInput):
        print("Running ExecutionStep...")
        print(f"SQL statement to execute: {data.sql_statement}")

        response = SQLite_exec_sql(data.sql_statement)
        console.print(response)

        execution_success = True
        if execution_success:
            print("SQL execution succeeded.")
            # Return success event and data instead of emitting event
            return SQLEvents.ExecutionSuccess, data.sql_statement
        else:
            error_description = "Execution error: Unable to run SQL."
            result = Execution2TableNames(
                user_query=data.user_query,
                table_names=data.table_names,
                column_names=data.column_names,
                sql_statement=data.sql_statement,
                error_description=error_description
            )
            # Return error event and data instead of emitting event
            return SQLEvents.ExecutionError, result