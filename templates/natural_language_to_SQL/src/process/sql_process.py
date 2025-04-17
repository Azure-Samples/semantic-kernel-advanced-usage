import sys

sys.path.append("../../")

# Import necessary components from the Semantic Kernel and our steps
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcess
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start

from src.models.step_models import TableNamesStepInput
from src.models.events import SQLEvents
from src.steps import (
    TableNameStep,
    ColumnNameStep,
    SQLGenerationStep,
    BusinessRulesStep,
    ValidationStep,
    ExecutionStep
)
from src.utils.step_tracker import get_tracker
from rich.console import Console
console = Console()



class SqlProcess():

    def __init__(self, kernel):
        self.kernel = kernel
        self.process = self.get_sql_process()
        # Initialize the step tracker with this process
        self.tracker = get_tracker().set_process(self.process)

    
    async def start(self, query):
        console.print(f"[green]Processing query:[/green] {query}")
        initial_input = TableNamesStepInput(user_query=query)
        
        # Reset tracker for a fresh start
        self.tracker.reset()
        
        # Start tracking the process start - using the async version
        await self.tracker.start_step_async("Process Start", initial_input)
    
        state = await start(
                process=self.process,
                kernel=self.kernel,
                initial_event=KernelProcessEvent(id=SQLEvents.StartProcess, data=initial_input)
            )
            
        # End the process tracking - using the async version
        await self.tracker.end_step_async(next_step="Process End")
        
        # Print the complete transition history
        self.tracker.print_transition_history()
        
        console.print("\n[green]Process completed![/green]")
        return state

    def get_sql_process(self) -> KernelProcess:
        """
        Build and configure the SQL generation process with all steps and their transitions.
        
        Returns:
            A fully configured KernelProcess instance ready to run
        """
        print("Building SQL Generation Process...")
        process = ProcessBuilder(name="SQLGenerationProcess")

        # Add steps to the process
        table_step = process.add_step(TableNameStep)
        print("Added TableNameStep to process.")
        column_step = process.add_step(ColumnNameStep)
        print("Added ColumnNameStep to process.")
        sql_generation_step = process.add_step(SQLGenerationStep)
        print("Added SQLGenerationStep to process.")
        business_rules_step = process.add_step(BusinessRulesStep)
        print("Added BusinessRulesStep to process.")
        validation_step = process.add_step(ValidationStep)
        print("Added ValidationStep to process.")
        execution_step = process.add_step(ExecutionStep)
        print("Added ExecutionStep to process.")

        # Define the process flow by connecting events to steps
        print("Defining process flow...")
        process.on_input_event(event_id=SQLEvents.StartProcess).send_event_to(target=table_step, parameter_name="data")
        print("Configured process flow: StartProcess -> TableNameStep.")
        
        table_step.on_event(event_id=SQLEvents.TableNameStepDone).send_event_to(
            target=column_step, parameter_name="data"
        )
        print("Configured process flow: TableNameStepDone -> ColumnNameStep.")
        
        column_step.on_event(event_id=SQLEvents.ColumnNameStepDone).send_event_to(
            target=sql_generation_step, parameter_name="data"
        )
        print("Configured process flow: ColumnNameStepDone -> SQLGenerationStep.")
        
        sql_generation_step.on_event(event_id=SQLEvents.SQLGenerationStepDone).send_event_to(
            target=business_rules_step, parameter_name="data"
        )
        print("Configured process flow: SQLGenerationStepDone -> BusinessRulesStep.")
        
        sql_generation_step.on_event(event_id=SQLEvents.SQLGenerationStepFailed).send_event_to(
            target=table_step, parameter_name="data"
        )
        print("Configured process flow: SQLGenerationStepFailed -> TableNameStep.")
        
        business_rules_step.on_event(event_id=SQLEvents.BusinessRulesStepDone).send_event_to(
            target=validation_step, parameter_name="data"
        )
        print("Configured process flow: BusinessRulesStepDone -> ValidationStep.")
        
        business_rules_step.on_event(event_id=SQLEvents.BusinessRulesFailed).send_event_to(
            target=sql_generation_step, parameter_name="data"
        )
        print("Configured process flow: BusinessRulesFailed -> SQLGenerationStep.")
        
        validation_step.on_event(event_id=SQLEvents.ValidationPassed).send_event_to(
            target=execution_step, parameter_name="data"
        )
        print("Configured process flow: ValidationPassed -> ExecutionStep.")
        
        validation_step.on_event(event_id=SQLEvents.ValidationFailed).send_event_to(
            target=sql_generation_step, parameter_name="data"
        )
        print("Configured process flow: ValidationFailed -> SQLGenerationStep.")
        
        execution_step.on_event(event_id=SQLEvents.ExecutionSuccess).stop_process()
        print("Configured process flow: ExecutionSuccess -> Stop Process.")
        
        execution_step.on_event(event_id=SQLEvents.ExecutionError).send_event_to(
            target=table_step, parameter_name="data"
        )
        print("Configured process flow: ExecutionError -> TableNameStep.")

        print("SQL Generation Process built successfully.")
        return process.build()
