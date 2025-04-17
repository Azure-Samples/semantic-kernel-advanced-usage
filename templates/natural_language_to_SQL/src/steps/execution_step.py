import sys
sys.path.append("../../")
import json
import os
from rich.console import Console
from semantic_kernel.kernel import Kernel

from src.models.events import SQLEvents
from src.models.step_models import ExecutionStepInput, Execution2TableNames
from src.utils import azure_sql_exec_sql
from src.utils.file_helpers import generate_unique_response_filename, clean_old_response_files
from src.steps.table_name_step import StepOutput

console = Console()

class ExecutionStep:
    """Execute SQL statement and return appropriate output."""
    async def invoke(self, kernel: Kernel, data: ExecutionStepInput):
        """Process the step and return the output with an event ID."""
        print("Running ExecutionStep...")
        print(f"SQL statement to execute: {data.sql_statement}")
        
        # Generate a unique response filename for this query
        response_filename = data.response_filename if hasattr(data, 'response_filename') and data.response_filename else generate_unique_response_filename(data.user_query)
        print(f"Using response file: {response_filename}")
        
        # Clean up old response files to prevent buildup
        clean_old_response_files()
        try:
            # Use Azure SQL execution instead of SQLite
            response = azure_sql_exec_sql(data.sql_statement)
            
            # Check if there was an error in the response
            if isinstance(response, dict) and "error" in response:
                error_msg = response["error"]
                print(f"SQL execution error: {error_msg}")
                
                # Check if this is a syntax error that needs Azure SQL-specific syntax
                is_syntax_error = any(syntax_text in error_msg.lower() for syntax_text in [
                    "syntax error", "incorrect syntax", "invalid column name", 
                    "invalid object name", "invalid identifier", "sql error", 
                    "invalid syntax", "near", "expected", "incorrect",
                    "fetch first", "top", "limit", "offset", "rownum"
                ])
                
                if is_syntax_error:
                    # This is a syntax error, so we should retry with Azure SQL syntax
                    print("Detected SQL syntax error that may require Azure SQL-specific syntax")
                    from src.models.step_models import SQLGenerationStepInput
                    
                    # Add specific note about the error and Azure SQL requirements
                    azure_sql_note = (
                        f"Previous SQL generated a syntax error in Azure SQL: {error_msg}\n"
                        f"Please modify the SQL to use Azure SQL syntax instead. Some key changes to consider:\n"
                        f"- Use TOP instead of FETCH FIRST/LIMIT\n"
                        f"- Use proper date formatting functions like CONVERT instead of non-standard functions\n"
                        f"- Ensure proper quoting of identifiers with square brackets []\n"
                        f"- Use OFFSET/FETCH for pagination instead of LIMIT/OFFSET\n"
                        f"- Follow T-SQL syntax for Azure SQL\n\n"
                        f"Original SQL that failed: {data.sql_statement}"
                    )
                    
                    # Create input for SQL generation retry
                    retry_input = SQLGenerationStepInput(
                        user_query=data.user_query,
                        table_column_names=data.table_column_names,
                        notes=azure_sql_note
                    )
                    
                    # Return to SQL generation step for retry
                    print("Returning to SQL generation step with Azure SQL requirements")
                    return StepOutput(id=SQLEvents.RetryWithAzureSQLSyntax, data=retry_input)
            
            # If we get here, execution was successful            console.print(response)
            print("SQL execution succeeded.")            
            resp_dd = {"query": data.user_query, "response": response, "filename": response_filename}

            console.print("resp_dd", resp_dd)            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(response_filename), exist_ok=True)
            
            # Write response to the unique file
            with open(response_filename, "w") as f:
                from src.utils.db_helpers import DecimalEncoder
                json.dump(resp_dd, f, indent=4, cls=DecimalEncoder)

            print(f"Execution success completed. Response saved to {response_filename}")
            
            # Include the response filename in the output so it can be used by subsequent steps
            response_with_filename = {"data": response, "response_filename": response_filename}
            return StepOutput(id=SQLEvents.ExecutionSuccess, data=response_with_filename)
            
        except Exception as e:
            error_description = f"Execution error: {str(e)}"
            try:
                # Ensure proper types for the Execution2TableNames model
                result = Execution2TableNames(
                    user_query=data.user_query,
                    table_names=data.table_names,
                    column_names=data.column_names if isinstance(data.column_names, list) else [],
                    sql_statement=data.sql_statement,
                    error_description=error_description
                )
            except Exception as validation_error:
                print(f"Error in creating Execution2TableNames: {validation_error}")
                # Create a fallback error result
                from src.models.step_models import GetTableNames
                fallback_table_names = GetTableNames(tables=[]) if data.table_names is None else data.table_names
                result = Execution2TableNames(
                    user_query=data.user_query if hasattr(data, 'user_query') else "Unknown query",
                    table_names=fallback_table_names,
                    column_names=[] if not hasattr(data, 'column_names') or not isinstance(data.column_names, list) else data.column_names,
                    sql_statement=data.sql_statement if hasattr(data, 'sql_statement') else "",
                    error_description=error_description
                )
                resp_dd = {"query": data.user_query, "response": error_description, "filename": response_filename}
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(response_filename), exist_ok=True)
                
            with open(response_filename, "w") as f:
                json.dump(resp_dd, f, indent=4)
            print(f"Execution error occurred. Error details saved to {response_filename}")
            
            # Include the response filename in the result
            result.response_filename = response_filename
            return StepOutput(id=SQLEvents.ExecutionError, data=result)