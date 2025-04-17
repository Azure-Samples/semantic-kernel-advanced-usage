import sys
sys.path.append("./")
sys.path.append("../")
sys.path.append("../src/")
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.utils.step_tracker import get_tracker, StepTracker
from src.process.sql_process import SqlProcess
from src.utils.chat_helpers import initialize_kernel

# Define the prompt template for final answer generation
prompt_template = """You are a helpful assistant, you will be given a query, and a context from our SQL database. Your task is to formulate a final answer based on the query and the context from the database.
Do NOT suggest any SQL queries or code, just provide the final answer.

Query: {{$query}}

DB Context:
{{$context}}

"""

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path to the frontend directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

# Mount the static files directory
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        print(f"Broadcasting message: {message.get('type')}")
        disconnected = []                

        try:
            connection = self.active_connections[-1]  # Send to the last connected client
            message['input_data'] = str(message.get('input_data', ''))
            message['output_data'] = str(message.get('output_data', ''))
            await connection.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            # disconnected.append(connection)
    
    # # Clean up disconnected sockets
    # for conn in disconnected:
    #     if conn in self.active_connections:
    #             self.active_connections.remove(conn)

manager = ConnectionManager()

# Models
class Step(BaseModel):
    id: str
    name: str
    description: str
    status: str = "pending"  # "pending", "active", or "completed"
    
class StepTransition(BaseModel):
    from_step: str
    to_step: str
    event: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    timestamp: str
    duration: Optional[float] = None

class QueryRequest(BaseModel):
    query: str

# Get process steps configuration
def get_process_steps():
    """Return the list of steps in the SQL process."""
    return [
        {
            "id": "process_start",
            "name": "Process Start",
            "description": "Initializes the process with the user query",
            "status": "pending"
        },
        {
            "id": "table_name_step",
            "name": "Table Name Step",
            "description": "Extracts relevant table names from the query",
            "status": "pending"
        },
        {
            "id": "column_name_step",
            "name": "Column Name Step",
            "description": "Identifies relevant columns from the selected tables",
            "status": "pending"
        },
        {
            "id": "sql_generation_step",
            "name": "SQL Generation Step",
            "description": "Generates the SQL statement based on tables and columns",
            "status": "pending"
        },
        {
            "id": "business_rules_step",
            "name": "Business Rules Step",
            "description": "Validates the SQL against business rules",
            "status": "pending"
        },
        {
            "id": "validation_step",
            "name": "Validation Step",
            "description": "Validates the SQL syntax and semantics",
            "status": "pending"
        },
        {
            "id": "execution_step",
            "name": "Execution Step",
            "description": "Executes the SQL against the database",
            "status": "pending"
        },
        {
            "id": "process_end",
            "name": "Process End",
            "description": "Completes the process and returns the result",
            "status": "pending"
        }
    ]

# Function to run a SQL process with the given query
async def run_sql_process(query: str):
    """Run the SQL process with the given query and generate a final answer."""
    try:
        # Broadcast process start
        await manager.broadcast({
            "type": "process_started",
            "query": query,
            "timestamp": datetime.now().isoformat()
        })
        
        # Initialize the kernel and SQL process
        kernel = await initialize_kernel()
        sql_process = SqlProcess(kernel)
        
        # Define a semantic function for generating the final answer
        final_answer_fn = kernel.add_function(
            prompt=prompt_template, 
            function_name="db_answer", 
            plugin_name="db_helper"
        )
        
        # Execute the SQL process
        await sql_process.start(query)
        
        # Get the results from the response.json file if available
        result = None
        sql_result = None
        if os.path.exists("response.json"):
            with open("response.json", "r") as f:
                result = json.load(f)
                sql_result = result["response"]
            
            # Track final answer generation in step tracker
            tracker = get_tracker()
            tracker.start_step("FinalAnswerGeneration", {"query": query, "sql_result": sql_result})
            
            # Generate the final answer
            final_answer = await kernel.invoke(final_answer_fn, query=query, context=str(sql_result))
            final_answer_text = str(final_answer)
            
            # Add the final answer to the result
            result["final_answer"] = final_answer_text
            
            # Update the response.json file with the final answer
            with open("response.json", "w") as f:
                json.dump(result, f, indent=4)
            
            # End final answer generation tracking
            tracker.end_step(next_step="Complete", next_event="AnswerGenerated", output_data=final_answer_text)
            
            # Broadcast the final answer
            await manager.broadcast({
                "type": "final_answer",
                "query": query,
                "answer": final_answer_text,
                "timestamp": datetime.now().isoformat()
            })
        
        # Broadcast process completion
        await manager.broadcast({
            "type": "process_completed",
            "query": query,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    except Exception as e:
        # Broadcast error
        await manager.broadcast({
            "type": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })
        raise e

# Register routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the index.html file"""
    with open(os.path.join(frontend_dir, "index.html"), "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api")
async def api_info():
    return {"message": "Natural Language to SQL Process Server API"}

@app.get("/api/steps")
async def get_steps_endpoint():
    """Get all steps in the process."""
    return get_process_steps()

@app.post("/api/submit-query")
async def submit_query(query_request: QueryRequest, background_tasks: BackgroundTasks):
    """Submit a natural language query to the SQL process."""
    # Reset the step tracker
    tracker = get_tracker()
    tracker.reset()
    
    # Run the SQL process in the background
    background_tasks.add_task(run_sql_process, query_request.query)
    
    return {
        "message": "Query submitted successfully",
        "query": query_request.query,
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial steps configuration
        await websocket.send_json({
            "type": "steps_configuration",
            "steps": get_process_steps()
        })
        
        # Get current tracker state and send history if available
        tracker = get_tracker()
        if tracker.transitions:
            await tracker.broadcast_transition_history()
        
        # Keep connection alive and listen for any messages
        while True:
            # print(">>>>>>>>>>>>>>>>>>>>>>>>>>", manager.active_connections)
            try:
                data = await websocket.receive_text()
            except  WebSocketDisconnect:
                print("WebSocket disconnected")
                tracker.reset()
                manager.disconnect(websocket)
                break
            # Process client messages
            if data == "get_history":
                await tracker.broadcast_transition_history()
            elif data.startswith("{"):
                # Try to parse JSON command
                try:
                    command = json.loads(data)
                    if command.get("type") == "reset" and command.get("command") == "clear_all_data":
                        print("Received reset command from client, clearing StepTracker state")
                        tracker.reset()
                        await websocket.send_json({
                            "type": "reset",
                            "timestamp": datetime.now().isoformat(),
                            "message": "StepTracker state has been reset"
                        })
                except Exception as e:
                    print(f"Error processing client command: {e}")
    except WebSocketDisconnect:
        tracker.reset()
        manager.disconnect(websocket)

# Initialize patching on startup
@app.on_event("startup")
async def startup_event():
    print("Starting up server...")
    print(f"Frontend directory: {frontend_dir}")
    print(f"Serving index.html from: {os.path.join(frontend_dir, 'index.html')}")
    
    # Connect the WebSocket manager to the StepTracker
    StepTracker.set_websocket_manager(manager)
    print("Connected WebSocket manager to StepTracker for real-time event broadcasting")

if __name__ == "__main__":
    import uvicorn
    # Run on port 80
    uvicorn.run(app, host="0.0.0.0", port=80)