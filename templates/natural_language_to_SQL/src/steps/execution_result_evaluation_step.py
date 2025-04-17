import sys
sys.path.append("../../")

from rich.console import Console
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions import kernel_function

from src.models.events import SQLEvents
from src.models.step_models import ExecutionStepInput, Execution2TableNames
from src.utils.db_helpers import SQLite_exec_sql
from src.utils.step_tracker import get_tracker

console = Console()

class ExecutionResultEvaluationStep(KernelProcessStep):

    """Execute SQL statement and emit appropriate event."""
    @kernel_function(name="execute_sql")
    async def evaluate_execution_result(self, context: KernelProcessStepContext, data: ExecutionStepInput, kernel: Kernel):
        # Get the step tracker and log the start of this step
        tracker = get_tracker()
        await tracker.start_step_async("Execution Result Evaluation", data)
        
        print("Running ExecutionStep...")
        console.print("[bold blue]SQL statement to execute:[/bold blue]", data.sql_statement)

        # Execute the SQL statement
        response = SQLite_exec_sql(data.sql_statement)
        console.print("[bold green]Execution Result:[/bold green]")
        console.print(response)

        execution_success = "error" not in response
        if execution_success:
            print("[bold green]SQL execution succeeded.[/bold green]")
            # Log transition to the console
            console.print("[bold cyan]Step Transition: Execution Result Evaluation → Success[/bold cyan]")
            
            # End the step with success
            await tracker.end_step_async("Process End", "ExecutionSuccess", response)
            
            # Emit event
            await context.emit_event(process_event=SQLEvents.ExecutionSuccess, data=data.sql_statement)
            print("Emitted event: ExecutionSuccess.")
        else:
            error_description = f"Execution error: {response.get('error', 'Unable to run SQL.')}"
            console.print(f"[bold red]{error_description}[/bold red]")
            
            # Log transition to the console
            console.print("[bold cyan]Step Transition: Execution Result Evaluation → Error[/bold cyan]")
            
            # Create result object with error
            result = Execution2TableNames(
                user_query=data.user_query,
                table_names=data.table_names,
                column_names=data.column_names,
                sql_statement=data.sql_statement,
                error_description=error_description
            )
            
            # End the step with error
            await tracker.end_step_async("Process End", "ExecutionError", {"error": error_description})
            
            # Emit event
            await context.emit_event(process_event=SQLEvents.ExecutionError, data=result)
            print("Emitted event: ExecutionError.")