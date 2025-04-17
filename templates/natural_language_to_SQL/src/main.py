import sys
import asyncio
from rich.console import Console
console = Console()
import json
import os
import sys
sys.path.append("./")
sys.path.append("../")

from src.process.sql_process import SqlProcess
from src.utils.chat_helpers import initialize_kernel
from src.utils.step_tracker import get_tracker

console = Console()

prompt_template = """You are a helpful assistant, you will be given a query, and a context from our SQL database. Your task is to formulate a final answer based on the query and the context from the database.
Do NOT suggest any SQL queries or code, just provide the final answer.

Query: {{$query}}

DB Context:
{{$context}}

"""

async def main():
    # Get query from command line argument
    if len(sys.argv) < 2:
        console.print("[red]Error: Please provide a query as a command line argument[/red]")
        console.print("Usage: python src/main.py \"your natural language query here\"")
        sys.exit(1)
        
    query = sys.argv[1]
    kernel = await initialize_kernel()

    # Define a semantic function (prompt) to generate a TL;DR summary
    final_answer_fn = kernel.add_function(
        prompt=prompt_template, 
        function_name="db_answer", 
        plugin_name="db_helper"
    )

    # Initialize the step tracker
    tracker = get_tracker()
    
    # Start tracking the whole process
    tracker.start_step("MainProcess", {"query": query})

    # Execute the SQL process
    sql_process = SqlProcess(kernel)
    await sql_process.start(query)    

    # Track SQL result retrieval
    tracker.start_step("ResultRetrieval", {"query": query})
    
    if os.path.exists("response.json"):
        with open("response.json", "r") as f:
            sql_result = f.read()
        sql_result = json.loads(sql_result)
        if sql_result["query"] == query:
            sql_result = sql_result["response"]
        else:            
            sql_result = "No response found."
    else:
        sql_result = "No response found."

    console.print("[purple]SQL Result:[/purple]")
    console.print(sql_result)
    
    # End SQL result retrieval tracking
    tracker.end_step(next_step="FinalAnswerGeneration", next_event="ResultRetrieved", output_data=sql_result)
    
    # Track final answer generation
    tracker.start_step("FinalAnswerGeneration", {"query": query, "sql_result": sql_result})
    
    final_answer = await kernel.invoke(final_answer_fn, query=query, context=str(sql_result))
    console.print("[green]Final Answer:[/green]")
    console.print(str(final_answer))
    
    # End final answer generation tracking
    tracker.end_step(next_step="Complete", next_event="AnswerGenerated", output_data=str(final_answer))
    
    # End the main process tracking
    tracker.end_step()
    
    # Print comprehensive statistics from the step tracker
    console.print("\n\n[bold magenta]============== COMPLETE PROCESS STATISTICS ==============[/bold magenta]")
    tracker.print_transition_history()
    
    # Print additional statistics
    step_history = tracker.get_transition_history()
    
    if step_history:
        # Calculate total steps executed
        console.print(f"\n[bold cyan]Total Steps Executed:[/bold cyan] {len(step_history)}")
        
        # Calculate total execution time
        if tracker.start_time:
            total_time = (datetime.now() - tracker.start_time).total_seconds()
            console.print(f"[bold cyan]Total Execution Time:[/bold cyan] {total_time:.3f}s")
        
        # Find slowest and fastest steps
        if len(step_history) > 0:
            step_times = [(t['step_name'], t['duration']) for t in step_history if 'duration' in t]
            if step_times:
                slowest = max(step_times, key=lambda x: x[1])
                fastest = min(step_times, key=lambda x: x[1])
                console.print(f"[bold cyan]Slowest Step:[/bold cyan] {slowest[0]} ({slowest[1]:.3f}s)")
                console.print(f"[bold cyan]Fastest Step:[/bold cyan] {fastest[0]} ({fastest[1]:.3f}s)")
        
        # Count transitions by type
        transitions = {}
        for t in step_history:
            if 'next_step' in t and t['next_step']:
                key = f"{t['step_name']} -> {t['next_step']}"
                transitions[key] = transitions.get(key, 0) + 1
        
        if transitions:
            console.print("\n[bold cyan]Transition Counts:[/bold cyan]")
            for transition, count in transitions.items():
                console.print(f"  {transition}: {count}")

    return final_answer

if __name__ == "__main__":
    # Import datetime here to avoid circular imports
    from datetime import datetime
    asyncio.run(main())
