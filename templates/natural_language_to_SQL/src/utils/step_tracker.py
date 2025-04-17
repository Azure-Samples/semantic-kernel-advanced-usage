import sys
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime
import json
import asyncio

sys.path.append("../../")

console = Console()

class StepTracker:
    """
    A singleton class that tracks step transitions in the SQL process.
    This allows monitoring the flow of data and transitions between steps.
    """
    _instance = None
    _websocket_manager = None  # Will be set by server.py

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StepTracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.transitions = []
        self.current_step = None
        self.process = None
        self.start_time = None
        self._listener_callbacks = []
        console.print("[bold purple]Step Tracker initialized[/bold purple]")
    
    @classmethod
    def set_websocket_manager(cls, manager):
        """Set the WebSocket connection manager for real-time broadcasting."""
        cls._websocket_manager = manager
        console.print("[bold cyan]WebSocket manager connected to StepTracker[/bold cyan]")
    
    def reset(self):
        """Reset the tracker state."""
        self.transitions = []
        self.current_step = None
        self.process = None
        self.start_time = datetime.now()
        console.print("[bold purple]Step Tracker reset[/bold purple]")
        
        # Broadcast reset event if WebSocket manager is available
        self._broadcast_event_async({
            "type": "reset",
            "timestamp": datetime.now().isoformat()
        })
        return self
    
    def add_listener(self, callback):
        """Add a listener callback that will be called for each transition."""
        self._listener_callbacks.append(callback)
        return self
    
    def set_process(self, process):
        """Set the SQL process instance to track."""
        self.process = process
        self.start_time = datetime.now()
        console.print(f"[bold green]Process tracking started at {self.start_time}[/bold green]")
        return self
    
    def _broadcast_event_async(self, event_data):
        """Broadcast an event to all connected WebSocket clients asynchronously."""
        if self._websocket_manager:
            try:
                # Create a task without waiting for it
                loop = asyncio.get_event_loop()
                loop.create_task(self._websocket_manager.broadcast(event_data))
                # print(">>>>>>>>>>>> Broadcasting event function:", event_data)
            except Exception as e:
                console.print(f"[bold red]Error broadcasting event: {e}[/bold red]")
    
    def start_step(self, step_name: str, data: Any = None):
        """Signal the start of a step with optional data arguments."""
        timestamp = datetime.now()
        self.current_step = {
            "step_name": step_name,
            "start_time": timestamp,
            "input_data": self._format_data(data),
            "status": "started"
        }
        
        console.print(f"[bold blue]STEP START: {step_name}[/bold blue] at {timestamp.strftime('%H:%M:%S.%f')[:-3]}")
        if data:
            console.print(Panel(self._format_data_pretty(data), title="Input Data", border_style="blue"))
        
        # Broadcast step start event to WebSocket clients
        step_id = step_name.replace(" ", "_").lower()
        self._broadcast_event_async({
            "type": "step_start",
            "step_id": step_id,
            "step_name": step_name,
            "timestamp": timestamp.isoformat(),
            "input_data": self._format_data(data)
        })
        # print(">>>>>>>>>>>> Broadcasting event start:", {"type": "step_start", 
        #                                            "step_id": step_id, 
        #                                            "step_name": step_name, 
        #                                            "timestamp": timestamp.isoformat(), 
        #                                            "input_data": self._format_data(data)})
        
        # Notify all listeners
        for callback in self._listener_callbacks:
            if callable(callback):
                try:
                    callback("step_start", step_name, data)
                except Exception as e:
                    console.print(f"[bold red]Error notifying listener: {e}[/bold red]")
        
        return self
    
    async def start_step_async(self, step_name: str, data: Any = None):
        """Async version of start_step."""
        self.start_step(step_name, data)
        return self
    
    def end_step(self, next_step: str = None, next_event: str = None, output_data: Any = None):
        """Signal the end of a step with transition information."""
        if not self.current_step:
            console.print("[bold red]Error: Cannot end step, no step currently active[/bold red]")
            return self
            
        timestamp = datetime.now()
        duration = timestamp - self.current_step["start_time"]
        
        transition = {
            **self.current_step,
            "end_time": timestamp,
            "duration": duration.total_seconds(),
            "next_step": next_step,
            "next_event": next_event,
            "output_data": self._format_data(output_data),
            "status": "completed"
        }
        
        # Insert at the beginning of the list instead of appending to the end
        self.transitions.insert(0, transition)
        
        console.print(f"[bold green]STEP END: {self.current_step['step_name']}[/bold green] " +
                    f"(Duration: {duration.total_seconds():.3f}s)")
        
        if next_step:
            console.print(f"[bold yellow]TRANSITION: {self.current_step['step_name']} -> {next_step} via {next_event}[/bold yellow]")
        
        if output_data:
            console.print(Panel(self._format_data_pretty(output_data), title="Output Data", border_style="green"))
            
        # Broadcast step transition event to WebSocket clients
        current_step_id = self.current_step["step_name"].replace(" ", "_").lower()
        next_step_id = next_step.replace(" ", "_").lower() if next_step else None
        
        self._broadcast_event_async({
            "type": "step_transition",
            "from_step_id": current_step_id,
            "to_step_id": next_step_id,
            "from_step": self.current_step["step_name"],
            "to_step": next_step,
            "event": next_event,
            "timestamp": timestamp.isoformat(),
            "duration": duration.total_seconds(),
            "output_data": self._format_data(output_data)
        })

        # print(">>>>>>>>>>>> Broadcasting event end:", {
        #     "type": "step_transition",
        #     "from_step_id": current_step_id,
        #     "to_step_id": next_step_id,
        #     "from_step": self.current_step["step_name"],
        #     "to_step": next_step,
        #     "event": next_event,
        #     "timestamp": timestamp.isoformat(), 
        #     "duration": duration.total_seconds(),
        #     "output_data": self._format_data(output_data)
        # })

            
        # Notify all listeners
        for callback in self._listener_callbacks:
            if callable(callback):
                try:
                    callback("step_end", self.current_step['step_name'], next_step, next_event, output_data, duration.total_seconds())
                except Exception as e:
                    console.print(f"[bold red]Error notifying listener: {e}[/bold red]")
            
        self.current_step = None
        return self
    
    async def end_step_async(self, next_step: str = None, next_event: str = None, output_data: Any = None):
        """Async version of end_step."""
        self.end_step(next_step, next_event, output_data)
        return self
    
    def _format_data(self, data):
        """Format data to be serializable in JSON."""
        if data is None:
            return None
        
        try:
            # Try to convert the data to a basic type for JSON serialization
            if hasattr(data, "to_dict"):
                return data.to_dict()
            elif hasattr(data, "__dict__"):
                return data.__dict__
            else:
                # Try to convert to string if all else fails
                return str(data)
        except Exception:
            return str(data)
    
    def _format_data_pretty(self, data: Any) -> str:
        """Format data for pretty console printing."""
        if data is None:
            return "None"
            
        try:
            # For objects with __dict__, show as pretty JSON
            if hasattr(data, '__dict__'):
                return json.dumps(data.__dict__, indent=2, default=str)
            # For dict objects, pretty print
            elif isinstance(data, dict):
                return json.dumps(data, indent=2, default=str)
            # For other objects, use str representation
            return str(data)
        except:
            return f"<Object of type {type(data).__name__}>"
    
    def print_transition_history(self):
        """Print the complete transition history of the process."""
        if not self.transitions:
            console.print("[yellow]No transitions recorded yet[/yellow]")
            return
            
        console.print("[bold purple]===== Process Transition History =====[/bold purple]")
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Step", style="dim")
        table.add_column("Status")
        table.add_column("Duration (s)")
        table.add_column("Next Step")
        table.add_column("Event")
        
        # Transitions are already in reverse order (newest first)
        for t in self.transitions:
            table.add_row(
                t["step_name"],
                t["status"],
                f"{t['duration']:.3f}",
                t["next_step"] or "End",
                t["next_event"] or "-"
            )
        
        console.print(table)
        
        # Calculate total duration
        if self.start_time:
            total_duration = (datetime.now() - self.start_time).total_seconds()
            console.print(f"[bold green]Total process duration: {total_duration:.3f}s[/bold green]")
    
    def get_transition_history(self) -> List[Dict]:
        """Return the transition history as a list of dictionaries."""
        return self.transitions
    
    def get_transition_history_serializable(self):
        """Return a serializable version of the transition history."""
        serializable_transitions = []
        for transition in self.transitions:
            serializable_transition = {
                "step_name": transition.get("step_name"),
                "next_step": transition.get("next_step"),
                "next_event": transition.get("next_event"),
                "timestamp": transition.get("start_time").isoformat() if transition.get("start_time") else None,
                "duration": transition.get("duration"),
                "status": transition.get("status", "completed"),
            }
            
            # Handle input and output data serialization
            if "input_data" in transition:
                serializable_transition["input_data"] = self._format_data(transition["input_data"])
            
            if "output_data" in transition:
                serializable_transition["output_data"] = self._format_data(transition["output_data"])
                
            serializable_transitions.append(serializable_transition)
        
        return serializable_transitions
    
    async def broadcast_transition_history(self):
        """Broadcast the full transition history to all connected WebSocket clients."""
        if self._websocket_manager:
            message = {
                "type": "transition_history",
                "transitions": self.get_transition_history_serializable()
            }
            await self._websocket_manager.broadcast(message)


# Factory function to get the singleton instance
def get_tracker() -> StepTracker:
    """Get the StepTracker singleton instance."""
    return StepTracker()