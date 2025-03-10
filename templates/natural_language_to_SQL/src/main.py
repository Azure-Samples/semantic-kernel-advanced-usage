import sys
import asyncio
from rich.console import Console
console = Console()
from semantic_kernel.kernel import Kernel

import sys
sys.path.append("./")
sys.path.append("../")

from src.process.sql_process import SqlProcess
from src.utils.chat_helpers import initialize_kernel



console = Console()

async def main():
    # Get query from command line argument
    if len(sys.argv) < 2:
        console.print("[red]Error: Please provide a query as a command line argument[/red]")
        console.print("Usage: python src/main.py \"your natural language query here\"")
        sys.exit(1)
        
    query = sys.argv[1]
    kernel = await initialize_kernel()
    sql_process = SqlProcess(kernel)
    await sql_process.start(query)    
    

if __name__ == "__main__":
    asyncio.run(main())
