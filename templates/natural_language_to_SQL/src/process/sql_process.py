import sys

sys.path.append("../../")

# Import our steps - we'll handle these directly instead of through a process architecture
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
from rich.console import Console
console = Console()

class SqlProcess():
    def __init__(self, kernel):
        self.kernel = kernel
        console.print("[green]SQL Process initialized[/green]")
    
    async def start(self, query):
        """
        Execute the SQL generation workflow directly instead of using the 
        process architecture from the older semantic-kernel version.
        """
        console.print(f"[green]Processing query:[/green] {query}")
        
        # Initialize with user query
        initial_input = TableNamesStepInput(user_query=query)
        
        # Create instances of each step
        table_name_step = TableNameStep()
        column_name_step = ColumnNameStep()
        sql_generation_step = SQLGenerationStep()
        business_rules_step = BusinessRulesStep()
        validation_step = ValidationStep()
        execution_step = ExecutionStep()
        
        try:
            # Execute each step in sequence
            console.print("[blue]Executing TableNameStep...[/blue]")
            table_output = await table_name_step.invoke(self.kernel, initial_input)
            
            console.print("[blue]Executing ColumnNameStep...[/blue]")
            column_output = await column_name_step.invoke(self.kernel, table_output.data)
            
            console.print("[blue]Executing SQLGenerationStep...[/blue]")
            sql_output = await sql_generation_step.invoke(self.kernel, column_output.data)
            
            # If SQL generation failed, retry with table names
            if hasattr(sql_output, 'id') and sql_output.id == SQLEvents.SQLGenerationStepFailed:
                console.print("[yellow]SQL Generation failed, retrying with table information...[/yellow]")
                sql_output = await sql_generation_step.invoke(self.kernel, table_output.data)
                if hasattr(sql_output, 'id') and sql_output.id == SQLEvents.SQLGenerationStepFailed:
                    console.print("[red]SQL Generation failed again. Stopping process.[/red]")
                    return None
            
            console.print("[blue]Executing BusinessRulesStep...[/blue]")
            business_rules_output = await business_rules_step.invoke(self.kernel, sql_output.data)
            
            # If business rules failed, regenerate SQL
            if hasattr(business_rules_output, 'id') and business_rules_output.id == SQLEvents.BusinessRulesFailed:
                console.print("[yellow]Business rules validation failed, regenerating SQL...[/yellow]")
                sql_output = await sql_generation_step.invoke(self.kernel, column_output.data)
                business_rules_output = await business_rules_step.invoke(self.kernel, sql_output.data)
                console.print("[blue]Executing ValidationStep...[/blue]")
            validation_output = await validation_step.invoke(self.kernel, business_rules_output.data)
            
            # If validation failed, regenerate SQL
            if hasattr(validation_output, 'id') and validation_output.id == SQLEvents.ValidationFailed:
                console.print("[yellow]SQL validation failed, regenerating SQL...[/yellow]")
                
                # If the validation output data is a SQLGenerationStepInput, use it for regeneration
                if hasattr(validation_output, 'data') and hasattr(validation_output.data, 'notes'):
                    # Use the enhanced notes from validation for better SQL generation
                    console.print("[blue]Using validation feedback for SQL regeneration...[/blue]")
                    sql_output = await sql_generation_step.invoke(self.kernel, validation_output.data)
                else:
                    # Fall back to original column data
                    sql_output = await sql_generation_step.invoke(self.kernel, column_output.data)
                
                # Process through business rules again
                console.print("[blue]Re-executing BusinessRulesStep after regeneration...[/blue]")
                business_rules_output = await business_rules_step.invoke(self.kernel, sql_output.data)
                
                # Validate the regenerated SQL
                console.print("[blue]Re-validating regenerated SQL...[/blue]")
                validation_output = await validation_step.invoke(self.kernel, business_rules_output.data)
                
                # Check if validation is still failing
                if hasattr(validation_output, 'id') and validation_output.id == SQLEvents.ValidationFailed:
                    console.print("[red]Validation still failing after regeneration. Check SQL generation.[/red]")
                    # Instead of proceeding to execution with invalid SQL, we could return early
                    # or try more regeneration attempts, but for now let's still proceed to show the error
            
            # Only proceed to execution if we have a ValidationPassed event or we have ExecutionStepInput
            if hasattr(validation_output, 'id') and validation_output.id == SQLEvents.ValidationPassed:
                console.print("[blue]Executing ExecutionStep...[/blue]")
                final_output = await execution_step.invoke(self.kernel, validation_output.data)
            elif hasattr(validation_output, 'data') and hasattr(validation_output.data, 'sql_statement'):
                console.print("[blue]Executing ExecutionStep with fallback validation...[/blue]")
                final_output = await execution_step.invoke(self.kernel, validation_output.data)
            else:
                console.print("[red]Cannot execute SQL as validation did not provide executable SQL.[/red]")
                return None              # Handle execution results
            if hasattr(final_output, 'id'):
                if final_output.id == SQLEvents.ExecutionSuccess:
                    console.print("[green]SQL executed successfully![/green]")
                elif final_output.id == SQLEvents.ExecutionError:
                    console.print("[red]SQL execution failed.[/red]")
                    
                    # Check for XML data type comparison error
                    xml_error = False
                    if hasattr(final_output, 'data') and hasattr(final_output.data, 'error'):
                        error_message = str(final_output.data.error)
                        if "XML data type cannot be compared or sorted" in error_message:
                            console.print("[yellow]XML data type comparison error detected - regenerating SQL...[/yellow]")
                            xml_error = True
                            # Create input for SQL generation with a note about avoiding XML comparisons
                            if hasattr(column_output, 'data'):
                                # Add a note to avoid XML comparisons
                                if hasattr(column_output.data, 'notes'):
                                    column_output.data.notes += " Avoid comparing or sorting XML data types in SQL statements."
                                # Regenerate SQL with the XML error note
                                sql_output = await sql_generation_step.invoke(self.kernel, column_output.data)
                                # Continue with business rules validation
                                business_rules_output = await business_rules_step.invoke(self.kernel, sql_output.data)
                                validation_output = await validation_step.invoke(self.kernel, business_rules_output.data)
                                final_output = await execution_step.invoke(self.kernel, validation_output.data)
                    
                    # If not XML error, try standard retry
                    if not xml_error:
                        # Retry with table information
                        table_output = await table_name_step.invoke(self.kernel, initial_input)
                        final_output = await self.retry_workflow(table_output.data)
                elif final_output.id == SQLEvents.RetryWithAzureSQLSyntax:
                    console.print("[yellow]SQL syntax error detected - retrying with Azure SQL syntax...[/yellow]")
                    # Retry with Azure SQL syntax adaptation
                    sql_output = await sql_generation_step.invoke(self.kernel, final_output.data)
                    if hasattr(sql_output, 'id') and sql_output.id == SQLEvents.SQLGenerationStepDone:
                        # Continue with business rules validation
                        business_rules_output = await business_rules_step.invoke(self.kernel, sql_output.data)
                        validation_output = await validation_step.invoke(self.kernel, business_rules_output.data)
                        final_output = await execution_step.invoke(self.kernel, validation_output.data)
                        
                        if hasattr(final_output, 'id') and final_output.id == SQLEvents.ExecutionSuccess:
                            console.print("[green]SQL executed successfully after Azure SQL syntax adaptation![/green]")
            
            console.print("\n[green]Process completed![/green]")
            return final_output
            
        except Exception as e:
            console.print(f"[red]Error in SQL process: {str(e)}[/red]")
            return None
    
    async def retry_workflow(self, data):
        """Helper method to retry the workflow from a certain point"""
        column_name_step = ColumnNameStep()
        sql_generation_step = SQLGenerationStep()
        business_rules_step = BusinessRulesStep()
        validation_step = ValidationStep()
        execution_step = ExecutionStep()
        
        column_output = await column_name_step.invoke(self.kernel, data)
        sql_output = await sql_generation_step.invoke(self.kernel, column_output.data)
        business_rules_output = await business_rules_step.invoke(self.kernel, sql_output.data)
        validation_output = await validation_step.invoke(self.kernel, business_rules_output.data)
        return await execution_step.invoke(self.kernel, validation_output.data)
