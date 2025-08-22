import click
import os
import sys
import importlib.util
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
import json
import glob
from pathlib import Path
import ast
import re

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

def discover_agents_and_workflows(search_paths: List[str] = None) -> Dict[str, Tuple[str, str]]:
    """
    Discover available agents and workflows from Python files using AST parsing.
    
    Returns:
        Dict mapping names to (file_path, type) tuples
    """
    if search_paths is None:
        # Default search paths
        search_paths = []
        
        # Look in examples directory
        tvara_root = Path(__file__).parent.parent
        examples_dir = tvara_root.parent / "examples"
        if examples_dir.exists():
            search_paths.append(str(examples_dir))
        
        # Look in current directory
        search_paths.append(".")
        
        # Look in common agent/workflow directories
        for common_dir in ["agents", "workflows", "tvara_agents", "tvara_workflows"]:
            if os.path.exists(common_dir):
                search_paths.append(common_dir)
    
    discovered = {}
    
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
            
        # Find all Python files
        py_files = glob.glob(os.path.join(search_path, "*.py"))
        py_files.extend(glob.glob(os.path.join(search_path, "**/*.py"), recursive=True))
        
        for py_file in py_files:
            if py_file.endswith("__init__.py") or "test_" in py_file:
                continue
                
            try:
                # First try AST parsing to avoid import errors
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for Agent and Workflow instantiations using multiple regex patterns
                agent_patterns = [
                    r'(\w+)\s*=\s*Agent\s*\([^)]*name\s*=\s*["\']([^"\']+)["\'][^)]*\)',
                    r'(\w+)\s*=\s*Agent\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
                    r'(\w+)\s*=\s*Agent\([^)]*name\s*=\s*["\']([^"\']+)["\']'
                ]
                
                workflow_patterns = [
                    r'(\w+)\s*=\s*Workflow\s*\([^)]*name\s*=\s*["\']([^"\']+)["\'][^)]*\)',
                    r'(\w+)\s*=\s*Workflow\s*\(\s*name\s*=\s*["\']([^"\']+)["\']',
                    r'(\w+)\s*=\s*Workflow\([^)]*name\s*=\s*["\']([^"\']+)["\']'
                ]
                
                agent_matches = []
                workflow_matches = []
                
                for pattern in agent_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    agent_matches.extend(matches)
                
                for pattern in workflow_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    workflow_matches.extend(matches)
                
                for var_name, agent_name in agent_matches:
                    name = agent_name.lower().replace(' ', '_').replace('-', '_')
                    discovered[name] = (py_file, 'agent')
                
                for var_name, workflow_name in workflow_matches:
                    name = workflow_name.lower().replace(' ', '_').replace('-', '_')
                    discovered[name] = (py_file, 'workflow')
                    
            except Exception:
                continue  # Skip files that cause errors
    
    return discovered

def resolve_agent_or_file(name_or_path: str) -> str:
    """
    Resolve a name or path to an actual file path.
    If it's a file path, return as-is.
    If it's a name, try to find it in discovered agents/workflows.
    """
    # If it's already a file path, return it
    if os.path.exists(name_or_path):
        return name_or_path
    
    # Try to discover by name
    discovered = discover_agents_and_workflows()
    if name_or_path in discovered:
        return discovered[name_or_path][0]
    
    # Try variations of the name
    variations = [
        name_or_path.lower().replace(' ', '_'),
        name_or_path.lower().replace('-', '_'),
        f"{name_or_path}_agent",
        f"{name_or_path}_workflow"
    ]
    
    for variation in variations:
        if variation in discovered:
            return discovered[variation][0]
    
    return name_or_path  # Return original if not found

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
@click.argument('target')  # Changed from file_path to target (can be file path or name)
@click.option('--port', '-p', default=8000, help='Port to run the server on')
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind the server to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--workers', default=1, help='Number of worker processes')
@click.option('--production', is_flag=True, help='Run in production mode with optimized settings')
@click.option('--daemon', is_flag=True, help='Run as background daemon')
@click.option('--log-level', default='warning', type=click.Choice(['debug', 'info', 'warning', 'error']), help='Log level')
def run(target: str, port: int, host: str, reload: bool, workers: int, production: bool, daemon: bool, log_level: str):
    """Run an agent or workflow as a REST API server
    
    TARGET: Path to Python file OR name of discovered agent/workflow
    
    Examples:
        tvara run my_agent.py --port 8000
        tvara run weather_agent --production
        tvara run sample_workflow --daemon --port 8080
    """
    try:
        # Resolve target to actual file path
        file_path = resolve_agent_or_file(target)
        
        if not os.path.exists(file_path):
            if file_path == target:
                click.echo(f"❌ Error: File '{target}' not found.", err=True)
                click.echo("💡 Use 'tvara list' to see available agents and workflows.", err=True)
            else:
                click.echo(f"❌ Error: Could not find agent or workflow named '{target}'.", err=True)
                click.echo("💡 Use 'tvara list' to see available agents and workflows.", err=True)
            sys.exit(1)
        
        # Apply production mode defaults
        if production:
            if workers == 1:  # Only override if not explicitly set
                workers = 4
            if host == '127.0.0.1':  # Only override if not explicitly set
                host = '0.0.0.0'
            log_level = 'info'
            reload = False  # Disable reload in production
            click.echo(f"🏭 Production mode enabled (workers: {workers}, host: {host})")
        
        try:
            server = TvaraServer(file_path)
        except Exception as e:
            click.echo(f"❌ Error loading {file_path}: {e}", err=True)
            sys.exit(1)
        
        if daemon:
            click.echo(f"🔥 Starting Tvara daemon on http://{host}:{port}")
            click.echo(f"📁 File: {file_path}")
            click.echo(f"🤖 Type: {server.execution_type.title()}")
            click.echo(f"📛 Name: {getattr(server.executable, 'name', 'Unknown')}")
            click.echo("⚠️  Daemon mode: Server running in background")
            
            # For daemon mode, we don't show the "Press Ctrl+C" message
            # and handle the process differently
            import subprocess
            
            # Create a script that will run the server
            script_content = f"""
import uvicorn
import sys
import os
sys.path.insert(0, '{os.path.dirname(os.path.abspath(file_path))}')

from tvara.cli.main import TvaraServer

server = TvaraServer('{file_path}')
uvicorn.run(
    server.app,
    host='{host}',
    port={port},
    reload={reload},
    workers={workers if not reload else 1},
    log_level='{log_level}'
)
"""
            
            # Write the script to a temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                temp_script = f.name
            
            try:
                # Start the process in background
                process = subprocess.Popen([
                    sys.executable, temp_script
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                click.echo(f"✅ Daemon started with PID: {process.pid}")
                click.echo(f"🌐 Access at: http://{host}:{port}")
                
                # Clean up temp file after a short delay
                import time
                time.sleep(1)
                os.unlink(temp_script)
                
            except Exception as e:
                click.echo(f"❌ Failed to start daemon: {e}", err=True)
                os.unlink(temp_script)
                sys.exit(1)
                
        else:
            click.echo(f"🚀 Starting Tvara server...")
            mode_info = []
            if production:
                mode_info.append("production")
            if reload:
                mode_info.append("dev/reload")
            
            mode_str = f" ({', '.join(mode_info)})" if mode_info else ""
            click.echo(f"🟢 Tvara running on http://{host}:{port}{mode_str}")
            click.echo("⏹️  Press Ctrl+C to stop the server")
            
            uvicorn.run(
                server.app,
                host=host,
                port=port,
                reload=reload,
                workers=workers if not reload else 1,
                log_level=log_level
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

@cli.command()
@click.option('--path', '-p', multiple=True, help='Additional paths to search for agents/workflows')
@click.option('--debug', is_flag=True, help='Show debug information')
def list(path, debug):
    """List available agents and workflows that can be run by name"""
    search_paths = list(path) if path else None
    
    if debug:
        # Show search paths for debugging
        if search_paths is None:
            tvara_root = Path(__file__).parent.parent
            examples_dir = tvara_root.parent / "examples"
            default_paths = [str(examples_dir), ".", "agents", "workflows", "tvara_agents", "tvara_workflows"]
            click.echo(f"🔍 Default search paths: {default_paths}")
            click.echo(f"📁 Examples dir exists: {examples_dir.exists()} at {examples_dir}")
        else:
            click.echo(f"🔍 Custom search paths: {list(search_paths)}")
    
    discovered = discover_agents_and_workflows(search_paths)
    
    if not discovered:
        click.echo("🔍 No agents or workflows found.")
        if not debug:
            click.echo("💡 Use --debug to see search paths.")
        click.echo("💡 Make sure you have Python files with Agent or Workflow instances.")
        return
    
    # Group by type
    agents = {k: v for k, v in discovered.items() if v[1] == 'agent'}
    workflows = {k: v for k, v in discovered.items() if v[1] == 'workflow'}
    
    click.echo("🤖 Available Agents and Workflows:\n")
    
    if agents:
        click.echo("📍 Agents:")
        for name, (file_path, _) in sorted(agents.items()):
            relative_path = os.path.relpath(file_path)
            click.echo(f"   {name:<20} → {relative_path}")
        click.echo()
    
    if workflows:
        click.echo("🔄 Workflows:")
        for name, (file_path, _) in sorted(workflows.items()):
            relative_path = os.path.relpath(file_path)
            click.echo(f"   {name:<20} → {relative_path}")
        click.echo()
    
    click.echo("🚀 Usage:")
    click.echo("   tvara run <name>           # Run by name")
    click.echo("   tvara run <file.py>        # Run by file path")
    click.echo("   tvara run <name> --production --workers 4")

@cli.command()
@click.argument('target')
@click.option('--output', '-o', default='Dockerfile', help='Output Dockerfile name')
def docker(target: str, output: str):
    """Generate a Dockerfile for deploying an agent or workflow
    
    TARGET: Path to Python file OR name of discovered agent/workflow
    """
    try:
        file_path = resolve_agent_or_file(target)
        
        if not os.path.exists(file_path):
            click.echo(f"❌ Error: Could not find '{target}'", err=True)
            sys.exit(1)
        
        # Load the agent/workflow to get info
        try:
            server = TvaraServer(file_path)
            executable_name = getattr(server.executable, 'name', 'tvara-app')
            executable_type = server.execution_type
        except Exception as e:
            click.echo(f"❌ Error loading {file_path}: {e}", err=True)
            sys.exit(1)
        
        # Generate Dockerfile content
        dockerfile_content = f"""# Dockerfile for {executable_name} ({executable_type})
# Generated by Tvara CLI

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt* ./
RUN pip install --no-cache-dir tvara[all]

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["tvara", "run", "{os.path.basename(file_path)}", "--production", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        # Write Dockerfile
        with open(output, 'w') as f:
            f.write(dockerfile_content)
        
        # Also create a .dockerignore if it doesn't exist
        dockerignore_content = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.env
.git/
.gitignore
README.md
.pytest_cache/
.coverage
.DS_Store
"""
        
        if not os.path.exists('.dockerignore'):
            with open('.dockerignore', 'w') as f:
                f.write(dockerignore_content)
            click.echo("📝 Created .dockerignore")
        
        click.echo(f"✅ Generated {output} for {executable_name}")
        click.echo(f"🐳 Build: docker build -t {executable_name.lower().replace(' ', '-')} .")
        click.echo(f"🚀 Run:   docker run -p 8000:8000 {executable_name.lower().replace(' ', '-')}")
        
    except Exception as e:
        click.echo(f"❌ Error generating Dockerfile: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli()
