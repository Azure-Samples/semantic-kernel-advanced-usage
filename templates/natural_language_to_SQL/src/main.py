import sys
import asyncio
from rich.console import Console
console = Console()
import json
import os
import sys
import glob
sys.path.append("./")
sys.path.append("../")

from src.process.sql_process import SqlProcess
from src.utils.chat_helpers import initialize_kernel
from src.utils.file_helpers import clean_old_response_files



console = Console()

prompt_template = """You are a helpful assistant, you will be given a query, and a context from our SQL database. Your task is to formulate a final answer based on the query and the context from the database.

If the context contains an error message (usually starting with "Execution error:"), you MUST acknowledge this in your answer. Do not attempt to provide a result when there is a SQL error. Instead, explain that there was an issue executing the query and briefly summarize the error if possible.

Query: {{$query}}

DB Context:
{{$context}}

"""

def find_latest_response_file(query=None):
    """
    Find the most recent response file that matches the given query.
    If no query is provided, returns the most recent response file.
    """
    # Create the response directory path
    response_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "responses")
    
    if not os.path.exists(response_dir):
        return None
    
    # Get all response files
    response_files = glob.glob(os.path.join(response_dir, "response_*.json"))
    
    if not response_files:
        return None
    
    # Sort by modification time (most recent first)
    response_files.sort(key=os.path.getmtime, reverse=True)
    
    if not query:
        # If no query specified, return the most recent file
        return response_files[0]
    
    # If query specified, look for matching files
    for file_path in response_files:
        try:
            with open(file_path, "r") as f:
                response_data = json.load(f)
                if "query" in response_data and response_data["query"] == query:
                    return file_path
        except (json.JSONDecodeError, IOError):
            continue
    
    # If no match found, return the most recent file
    return response_files[0]



async def main():
    # Get query from command line argument
    if len(sys.argv) < 2:
        console.print("[red]Error: Please provide a query as a command line argument[/red]")
        console.print("Usage: python src/main.py \"your natural language query here\"")
        sys.exit(1)
        
    query = sys.argv[1]
    kernel = await initialize_kernel()

    # Clean up old response files to prevent buildup
    clean_old_response_files()

    # For older versions of SK, use register_semantic_function
    try:
        # Try direct chat completion with the query
        sql_process = SqlProcess(kernel)
        process_result = await sql_process.start(query)    

        sql_result = "No response found."
        
        # Find the latest response file that matches this query
        response_file = None
        
        # If the process returned a filename, use that
        if hasattr(process_result, 'data') and hasattr(process_result.data, 'response_filename'):
            response_file = process_result.data.response_filename
        else:
            # Otherwise try to find the latest response file for this query
            response_file = find_latest_response_file(query)
        
        if response_file and os.path.exists(response_file):
            try:
                with open(response_file, "r") as f:
                    file_content = f.read()
                
                try:
                    sql_result_json = json.loads(file_content)
                    if sql_result_json["query"] == query:
                        sql_result = sql_result_json["response"]
                        console.print(f"[green]Found matching response in file: {os.path.basename(response_file)}[/green]")
                    else:            
                        console.print("[yellow]Warning: Response doesn't match the current query[/yellow]")
                except json.JSONDecodeError as e:
                    console.print(f"[red]Error parsing JSON response: {str(e)}[/red]")
                    console.print("[yellow]Using raw file content as response[/yellow]")
                    sql_result = file_content
            except Exception as e:
                console.print(f"[red]Error reading response file {response_file}: {str(e)}[/red]")
        else:
            console.print("[yellow]No matching response file found[/yellow]")

        console.print("[purple]SQL Result:[/purple]")
        console.print(sql_result)

        # Use direct chat service to get the final answer
        from src.utils.chat_helpers import call_chat_completion
        
        final_prompt = prompt_template.replace("{{$query}}", query).replace("{{$context}}", str(sql_result))
        final_answer = await call_chat_completion(kernel, final_prompt)
        
        console.print("[green]Final Answer:[/green]")
        console.print(str(final_answer))

        return final_answer
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return f"Error: {str(e)}"
    

if __name__ == "__main__":
    asyncio.run(main())
