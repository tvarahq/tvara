import click
import os
import sys
import importlib.util
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
import json

class ExecutionRequest(BaseModel):
    input: str

class ExecutionResponse(BaseModel):
    result: str
    summary: Optional[str] = None
    status: str = "success"
    execution_type: str
    success: Optional[bool] = None
    agent_outputs: Optional[list] = None
    error: Optional[str] = None

class TvaraServer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.executable = self._load_executable(file_path)
        self.execution_type = self._determine_type()
        self.app = FastAPI(
            title="Tvara Server",
            description=f"Serving {self.execution_type}: {getattr(self.executable, 'name', 'Unknown')}"
        )
        self._setup_routes()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _load_executable(self, file_path: str):
        """Load agent or workflow from Python file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        spec = importlib.util.spec_from_file_location("executable_module", file_path)
        executable_module = importlib.util.module_from_spec(spec)
        
        file_dir = os.path.dirname(os.path.abspath(file_path))
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)
        
        try:
            spec.loader.exec_module(executable_module)
        except Exception as e:
            raise ImportError(f"Error loading file: {e}\n{traceback.format_exc()}")
        
        workflows = []
        agents = []
        
        for attr_name in dir(executable_module):
            attr = getattr(executable_module, attr_name)
            if hasattr(attr, 'run') and hasattr(attr, 'name') and hasattr(attr, '__class__'):
                class_name = attr.__class__.__name__
                if class_name == 'Workflow':
                    workflows.append(attr)
                elif class_name == 'Agent':
                    agents.append(attr)
        
        if workflows:
            return workflows[0]
        elif agents:
            return agents[0]
        
        candidates = []
        for attr_name in dir(executable_module):
            attr = getattr(executable_module, attr_name)
            if hasattr(attr, 'run') and not attr_name.startswith('_'):
                candidates.append(attr)
        
        if not candidates:
            raise ValueError(
                "No Agent or Workflow found in the file. "
                "Make sure your file contains an Agent or Workflow instance with a 'run' method."
            )
        
        return candidates[0]

    def _determine_type(self):
        """Determine if the executable is an Agent or Workflow"""
        class_name = self.executable.__class__.__name__
        if class_name == 'Agent':
            return 'agent'
        elif class_name == 'Workflow':
            return 'workflow'
        else:
            return 'unknown'
    
    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {
                "message": f"Tvara Server - {getattr(self.executable, 'name', 'Unknown')}",
                "type": self.execution_type,
                "endpoints": {
                    "POST /run": "Execute the agent/workflow",
                    "GET /health": "Health check",
                    "GET /info": "Detailed information"
                }
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "name": getattr(self.executable, 'name', 'Unknown'),
                "type": self.execution_type
            }
        
        @self.app.get("/info")
        async def info():
            info_data = {
                "name": getattr(self.executable, 'name', 'Unknown'),
                "type": self.execution_type,
                "class": self.executable.__class__.__name__,
                "file_path": self.file_path
            }
            
            if self.execution_type == 'agent':
                info_data.update({
                    "model": getattr(self.executable, 'model', 'Unknown'),
                    "tools": [tool.name for tool in getattr(self.executable, 'tools', [])],
                    "connectors": [conn.name for conn in getattr(self.executable, 'connectors', [])]
                })
            elif self.execution_type == 'workflow':
                agents = getattr(self.executable, 'agents', [])
                info_data.update({
                    "mode": getattr(self.executable, 'mode', 'Unknown').value if hasattr(getattr(self.executable, 'mode', None), 'value') else getattr(self.executable, 'mode', 'Unknown'),
                    "max_iterations": getattr(self.executable, 'max_iterations', 'Unknown'),
                    "agent_count": len(agents),
                    "agents": [getattr(agent, 'name', f'Agent_{i}') for i, agent in enumerate(agents)],
                    "has_manager": getattr(self.executable, 'manager_agent', None) is not None,
                    "manager_name": getattr(getattr(self.executable, 'manager_agent', None), 'name', None)
                })
            
            return info_data
        
        @self.app.post("/run", response_model=ExecutionResponse)
        async def run_executable(request: ExecutionRequest):
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor, 
                    self._execute, 
                    request.input
                )
                
                if self.execution_type == 'workflow':
                    if hasattr(result, 'success') and hasattr(result, 'final_output'):
                        summary = None
                        if hasattr(self.executable, 'get_workflow_summary'):
                            try:
                                summary_data = self.executable.get_workflow_summary()
                                if isinstance(summary_data, dict):
                                    summary = json.dumps(summary_data, indent=2)
                                else:
                                    summary = str(summary_data) if summary_data else None
                            except:
                                pass
                        
                        return ExecutionResponse(
                            result=result.final_output,
                            summary=summary,
                            status="success" if result.success else "error",
                            execution_type=self.execution_type,
                            success=result.success,
                            agent_outputs=result.agent_outputs,
                            error=result.error
                        )
                    else:
                        return ExecutionResponse(
                            result=str(result),
                            status="success",
                            execution_type=self.execution_type
                        )
                else:
                    return ExecutionResponse(
                        result=str(result),
                        status="success",
                        execution_type=self.execution_type
                    )
            
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"{self.execution_type.title()} execution failed: {str(e)}"
                )
    
    def _execute(self, input_text: str):
        """Execute agent or workflow in a separate thread"""
        try:
            return self.executable.run(input_text)
        except Exception as e:
            raise Exception(f"Execution error: {str(e)}\n{traceback.format_exc()}")

@click.group()
def cli():
    """Tvara CLI - Run agents and workflows as REST API services"""
    pass

@cli.command()
@click.argument('file_path')
@click.option('--port', '-p', default=8000, help='Port to run the server on')
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind the server to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--workers', default=1, help='Number of worker processes')
def run(file_path: str, port: int, host: str, reload: bool, workers: int):
    """Run an agent or workflow as a REST API server
    
    FILE_PATH: Path to Python file containing Agent or Workflow instance
    
    Examples:
        tvara run my_agent.py --port 8000
        tvara run my_workflow.py --host 0.0.0.0 --port 8080
        tvara run agents/slack_agent.py --reload
    """
    try:
        if not os.path.exists(file_path):
            click.echo(f"❌ Error: File '{file_path}' not found.", err=True)
            sys.exit(1)
        
        try:
            server = TvaraServer(file_path)
        except Exception as e:
            click.echo(f"❌ Error loading {file_path}: {e}", err=True)
            sys.exit(1)
        
        click.echo(f"🚀 Starting Tvara server...")
        # click.echo(f"📁 File: {file_path}")
        # click.echo(f"🤖 Type: {server.execution_type.title()}")
        # click.echo(f"📛 Name: {getattr(server.executable, 'name', 'Unknown')}")
        # click.echo(f"🌐 Server: http://{host}:{port}")
        # click.echo()
        # click.echo("📍 Available endpoints:")
        # click.echo("   GET  /          - Server info")
        # click.echo("   GET  /health    - Health check")
        # click.echo("   GET  /info      - Detailed information")
        # click.echo("   POST /run       - Execute agent/workflow")
        # click.echo("   GET  /docs      - API documentation (Swagger UI)")
        # click.echo()
        # click.echo("🔥 Example usage:")
        # click.echo(f'   curl -X POST http://{host}:{port}/run \\')
        # click.echo('     -H "Content-Type: application/json" \\')
        # click.echo('     -d \'{"input": "Your request here"}\'')
        # click.echo()
        # click.echo("⏹️  Press Ctrl+C to stop the server")
        click.echo(f"🟢 Tvara running on http://{host}:{port}")
        click.echo("⏹️  Press Ctrl+C to stop the server")
        
        uvicorn.run(
            server.app,
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="warning"
        )
        
    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped by user")
    except Exception as e:
        click.echo(f"❌ Error starting server: {e}", err=True)
        sys.exit(1)

@cli.command()
def version():
    """Show Tvara version"""
    try:
        import tvara
        click.echo(f"Tvara version: {tvara.__version__}")
    except:
        click.echo("Tvara version: Unknown")

if __name__ == "__main__":
    cli()
