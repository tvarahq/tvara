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
from pathlib import Path
import shutil

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

@cli.group()
def deploy():
    """Deploy agents and workflows in various modes"""
    pass

@deploy.command()
@click.argument('file_path')
@click.option('--output-dir', '-o', default='./deployment', help='Output directory for deployment artifacts')
@click.option('--image-name', default=None, help='Docker image name (defaults to filename)')
@click.option('--port', '-p', default=8000, help='Port to expose in container')
@click.option('--env-file', default='.env', help='Environment file to copy')
def docker(file_path: str, output_dir: str, image_name: str, port: int, env_file: str):
    """Generate Docker deployment artifacts for an agent or workflow
    
    FILE_PATH: Path to Python file containing Agent or Workflow instance
    
    Examples:
        tvara deploy docker my_agent.py
        tvara deploy docker my_workflow.py --output-dir ./docker-deploy
        tvara deploy docker agents/slack_agent.py --image-name slack-agent --port 8080
    """
    try:
        if not os.path.exists(file_path):
            click.echo(f"❌ Error: File '{file_path}' not found.", err=True)
            sys.exit(1)
        
        # Validate the file contains a valid agent or workflow
        try:
            server = TvaraServer(file_path)
            executable_name = getattr(server.executable, 'name', 'Unknown')
            executable_type = server.execution_type
        except Exception as e:
            click.echo(f"❌ Error loading {file_path}: {e}", err=True)
            sys.exit(1)
        
        # Set default image name if not provided
        if not image_name:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            image_name = base_name.replace('_', '-').lower()
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        click.echo(f"🐳 Generating Docker deployment for {executable_type}: {executable_name}")
        click.echo(f"📁 Output directory: {output_path.absolute()}")
        
        # Copy the agent/workflow file
        src_file = Path(file_path)
        dest_file = output_path / src_file.name
        shutil.copy2(src_file, dest_file)
        
        # Copy environment file if it exists
        if os.path.exists(env_file):
            shutil.copy2(env_file, output_path / '.env')
            click.echo(f"📄 Copied environment file: {env_file}")
        else:
            click.echo(f"⚠️  Environment file '{env_file}' not found, creating template")
            _create_env_template(output_path / '.env.template')
        
        # Generate Dockerfile
        dockerfile_content = _generate_dockerfile(src_file.name, port)
        (output_path / 'Dockerfile').write_text(dockerfile_content)
        
        # Generate docker-compose.yml
        compose_content = _generate_docker_compose(image_name, port, executable_name, executable_type)
        (output_path / 'docker-compose.yml').write_text(compose_content)
        
        # Generate deployment script
        deploy_script = _generate_deploy_script(image_name)
        script_path = output_path / 'deploy.sh'
        script_path.write_text(deploy_script)
        script_path.chmod(0o755)
        
        # Generate README
        readme_content = _generate_deployment_readme(image_name, port, executable_name, executable_type)
        (output_path / 'README.md').write_text(readme_content)
        
        click.echo(f"✅ Docker deployment artifacts generated successfully!")
        click.echo(f"🗂️  Generated files:")
        click.echo(f"   • {dest_file.name} - {executable_type.title()} file")
        click.echo(f"   • Dockerfile - Container image definition")
        click.echo(f"   • docker-compose.yml - Service orchestration")
        click.echo(f"   • deploy.sh - Deployment script")
        click.echo(f"   • README.md - Deployment instructions")
        click.echo()
        click.echo(f"🚀 To deploy:")
        click.echo(f"   cd {output_dir}")
        click.echo(f"   ./deploy.sh")
        click.echo()
        click.echo(f"🌐 Service will be available at: http://localhost:{port}")
        
    except Exception as e:
        click.echo(f"❌ Error generating Docker deployment: {e}", err=True)
        sys.exit(1)

@deploy.command()
@click.argument('file_path')
@click.option('--output-dir', '-o', default='./production', help='Output directory for production artifacts')
@click.option('--port', '-p', default=8000, help='Port for the service')
@click.option('--host', '-h', default='0.0.0.0', help='Host to bind to')
@click.option('--workers', '-w', default=4, help='Number of worker processes')
def production(file_path: str, output_dir: str, port: int, host: str, workers: int):
    """Generate production deployment configuration
    
    FILE_PATH: Path to Python file containing Agent or Workflow instance
    
    Examples:
        tvara deploy production my_agent.py
        tvara deploy production my_workflow.py --workers 8 --port 8080
    """
    try:
        if not os.path.exists(file_path):
            click.echo(f"❌ Error: File '{file_path}' not found.", err=True)
            sys.exit(1)
        
        # Validate the file contains a valid agent or workflow
        try:
            server = TvaraServer(file_path)
            executable_name = getattr(server.executable, 'name', 'Unknown')
            executable_type = server.execution_type
        except Exception as e:
            click.echo(f"❌ Error loading {file_path}: {e}", err=True)
            sys.exit(1)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        click.echo(f"🏭 Generating production deployment for {executable_type}: {executable_name}")
        click.echo(f"📁 Output directory: {output_path.absolute()}")
        
        # Copy the agent/workflow file
        src_file = Path(file_path)
        dest_file = output_path / src_file.name
        shutil.copy2(src_file, dest_file)
        
        # Generate production configuration
        prod_config = _generate_production_config(dest_file.name, host, port, workers)
        (output_path / 'tvara-config.yaml').write_text(prod_config)
        
        # Generate systemd service file
        service_name = f"tvara-{os.path.splitext(src_file.name)[0]}"
        systemd_content = _generate_systemd_service(service_name, output_path.absolute(), dest_file.name, host, port, workers)
        (output_path / f'{service_name}.service').write_text(systemd_content)
        
        # Generate start/stop scripts
        start_script = _generate_start_script(dest_file.name, host, port, workers)
        (output_path / 'start.sh').write_text(start_script)
        (output_path / 'start.sh').chmod(0o755)
        
        stop_script = _generate_stop_script()
        (output_path / 'stop.sh').write_text(stop_script)
        (output_path / 'stop.sh').chmod(0o755)
        
        # Generate production README
        prod_readme = _generate_production_readme(service_name, executable_name, executable_type, host, port, workers)
        (output_path / 'README-production.md').write_text(prod_readme)
        
        click.echo(f"✅ Production deployment artifacts generated successfully!")
        click.echo(f"🗂️  Generated files:")
        click.echo(f"   • {dest_file.name} - {executable_type.title()} file")
        click.echo(f"   • tvara-config.yaml - Production configuration")
        click.echo(f"   • {service_name}.service - Systemd service file")
        click.echo(f"   • start.sh / stop.sh - Control scripts")
        click.echo(f"   • README-production.md - Production deployment guide")
        click.echo()
        click.echo(f"🚀 To deploy:")
        click.echo(f"   cd {output_dir}")
        click.echo(f"   ./start.sh")
        click.echo()
        click.echo(f"🌐 Service will be available at: http://{host}:{port}")
        
    except Exception as e:
        click.echo(f"❌ Error generating production deployment: {e}", err=True)
        sys.exit(1)

def _create_env_template(file_path: Path):
    """Create a template environment file"""
    template_content = """# Tvara Environment Configuration Template
# Copy this file to .env and fill in your API keys

# Required: LLM API Keys (use one or more)
MODEL_API_KEY=your_gemini_or_openai_or_claude_key

# Required for tools: Composio API Key
COMPOSIO_API_KEY=your_composio_api_key

# Optional: Additional service API keys
TAVILY_API_KEY=your_tavily_api_key

# Optional: Deployment configuration
TVARA_HOST=0.0.0.0
TVARA_PORT=8000
TVARA_WORKERS=1
"""
    file_path.write_text(template_content)

def _generate_dockerfile(app_file: str, port: int) -> str:
    """Generate Dockerfile content"""
    return f"""# Tvara Agent/Workflow Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt* ./
RUN pip install tvara uvicorn fastapi click

# Copy application files
COPY {app_file} ./
COPY .env* ./

# Expose port
EXPOSE {port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

# Run the application
CMD ["tvara", "run", "{app_file}", "--host", "0.0.0.0", "--port", "{port}"]
"""

def _generate_docker_compose(image_name: str, port: int, app_name: str, app_type: str) -> str:
    """Generate docker-compose.yml content"""
    return f"""# Tvara {app_type.title()}: {app_name}
version: '3.8'

services:
  {image_name}:
    build: .
    image: {image_name}:latest
    container_name: {image_name}
    ports:
      - "{port}:{port}"
    environment:
      - TVARA_HOST=0.0.0.0
      - TVARA_PORT={port}
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - ./logs:/app/logs
    networks:
      - tvara-network

networks:
  tvara-network:
    driver: bridge

volumes:
  logs:
    driver: local
"""

def _generate_deploy_script(image_name: str) -> str:
    """Generate deployment script"""
    return f"""#!/bin/bash
# Tvara Deployment Script

set -e

echo "🐳 Building and deploying {image_name}..."

# Build the Docker image
echo "📦 Building Docker image..."
docker-compose build

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for service to be healthy..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

echo "✅ Deployment completed successfully!"
echo "🌐 Service is available at the configured port"
echo ""
echo "📋 Useful commands:"
echo "   docker-compose logs -f        # View logs"
echo "   docker-compose ps             # Check status"
echo "   docker-compose down           # Stop services"
echo "   docker-compose restart        # Restart services"
"""

def _generate_production_config(app_file: str, host: str, port: int, workers: int) -> str:
    """Generate production YAML configuration"""
    return f"""# Tvara Production Configuration
server:
  host: "{host}"
  port: {port}
  workers: {workers}
  reload: false
  log_level: "info"
  
application:
  file: "{app_file}"
  
deployment:
  environment: "production"
  health_check_interval: 30
  timeout: 60
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/tvara.log"
  
monitoring:
  enable_metrics: true
  metrics_port: 9090
"""

def _generate_systemd_service(service_name: str, work_dir: Path, app_file: str, host: str, port: int, workers: int) -> str:
    """Generate systemd service file"""
    return f"""[Unit]
Description=Tvara {service_name} Service
After=network.target

[Service]
Type=forking
User=tvara
Group=tvara
WorkingDirectory={work_dir}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=TVARA_ENV=production
ExecStart=/usr/local/bin/tvara run {app_file} --host {host} --port {port} --workers {workers}
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

def _generate_start_script(app_file: str, host: str, port: int, workers: int) -> str:
    """Generate start script"""
    return f"""#!/bin/bash
# Tvara Production Start Script

set -e

echo "🏭 Starting Tvara in production mode..."

# Create logs directory
mkdir -p logs

# Start the service
nohup tvara run {app_file} \\
    --host {host} \\
    --port {port} \\
    --workers {workers} \\
    > logs/tvara.log 2>&1 &

echo $! > tvara.pid

echo "✅ Tvara started successfully!"
echo "📋 Process ID: $(cat tvara.pid)"
echo "🌐 Service: http://{host}:{port}"
echo "📄 Logs: tail -f logs/tvara.log"
"""

def _generate_stop_script() -> str:
    """Generate stop script"""
    return """#!/bin/bash
# Tvara Production Stop Script

if [ -f tvara.pid ]; then
    PID=$(cat tvara.pid)
    echo "🛑 Stopping Tvara (PID: $PID)..."
    kill $PID
    rm -f tvara.pid
    echo "✅ Tvara stopped successfully!"
else
    echo "❌ PID file not found. Service may not be running."
fi
"""

def _generate_deployment_readme(image_name: str, port: int, app_name: str, app_type: str) -> str:
    """Generate deployment README"""
    return f"""# Tvara Docker Deployment

This directory contains Docker deployment artifacts for your Tvara {app_type}: **{app_name}**.

## Quick Start

1. **Configure environment** (if .env doesn't exist):
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

2. **Deploy with Docker Compose**:
   ```bash
   ./deploy.sh
   ```

3. **Access your service**:
   - Service: http://localhost:{port}
   - API Docs: http://localhost:{port}/docs
   - Health Check: http://localhost:{port}/health

## Manual Deployment

### Build and Run
```bash
# Build the image
docker build -t {image_name} .

# Run the container
docker run -d \\
  --name {image_name} \\
  --env-file .env \\
  -p {port}:{port} \\
  {image_name}
```

### Using Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /info` - Detailed {app_type} information
- `POST /run` - Execute the {app_type}

## Example Usage

```bash
# Test the health endpoint
curl http://localhost:{port}/health

# Execute the {app_type}
curl -X POST http://localhost:{port}/run \\
  -H "Content-Type: application/json" \\
  -d '{{"input": "Your request here"}}'
```

## Environment Variables

Make sure your `.env` file contains:

```env
MODEL_API_KEY=your_api_key_here
COMPOSIO_API_KEY=your_composio_key_here
```

## Monitoring

- **Logs**: `docker-compose logs -f {image_name}`
- **Status**: `docker-compose ps`
- **Health**: `curl http://localhost:{port}/health`

## Scaling

To scale your service:

```bash
# Scale to multiple instances
docker-compose up -d --scale {image_name}=3

# Use a load balancer (nginx, traefik, etc.) to distribute traffic
```

## Troubleshooting

1. **Service not starting**: Check logs with `docker-compose logs {image_name}`
2. **Environment issues**: Verify `.env` file has correct API keys
3. **Port conflicts**: Change port in `docker-compose.yml` and restart

## Production Considerations

- Use environment-specific `.env` files
- Set up proper logging and monitoring
- Configure reverse proxy (nginx) for SSL termination
- Implement backup strategies for persistent data
- Consider using orchestration platforms (Kubernetes, Docker Swarm)
"""

def _generate_production_readme(service_name: str, app_name: str, app_type: str, host: str, port: int, workers: int) -> str:
    """Generate production README"""
    return f"""# Tvara Production Deployment

Production deployment configuration for your Tvara {app_type}: **{app_name}**.

## Quick Start

1. **Start the service**:
   ```bash
   ./start.sh
   ```

2. **Access your service**:
   - Service: http://{host}:{port}
   - Workers: {workers}

## Production Setup

### Option 1: Using Start/Stop Scripts

```bash
# Start the service
./start.sh

# Stop the service  
./stop.sh

# Check logs
tail -f logs/tvara.log
```

### Option 2: Using Systemd

```bash
# Copy service file
sudo cp {service_name}.service /etc/systemd/system/

# Create tvara user
sudo useradd -r -s /bin/false tvara

# Set permissions
sudo chown -R tvara:tvara /path/to/this/directory

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable {service_name}
sudo systemctl start {service_name}

# Check status
sudo systemctl status {service_name}
```

## Configuration

The `tvara-config.yaml` file contains production settings:

- **Host**: {host}
- **Port**: {port}  
- **Workers**: {workers}
- **Environment**: Production
- **Logging**: Configured for production

## Monitoring

### Service Status
```bash
# If using systemd
sudo systemctl status {service_name}

# If using scripts
ps aux | grep tvara
```

### Logs
```bash
# Application logs
tail -f logs/tvara.log

# System logs (if using systemd)
sudo journalctl -u {service_name} -f
```

### Health Checks
```bash
curl http://{host}:{port}/health
```

## Scaling

### Vertical Scaling
- Increase `workers` in configuration
- Restart the service

### Horizontal Scaling
- Deploy multiple instances on different ports
- Use a load balancer (nginx, HAProxy)

## Security

1. **Firewall**: Configure firewall to allow only necessary ports
2. **SSL/TLS**: Use reverse proxy for HTTPS termination
3. **Environment**: Store sensitive keys in secure location
4. **User**: Run service as non-root user (tvara)

## Load Balancing (nginx example)

```nginx
upstream tvara_backend {{
    server 127.0.0.1:{port};
    # Add more instances as needed
}}

server {{
    listen 80;
    server_name your-domain.com;

    location / {{
        proxy_pass http://tvara_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
```

## Backup and Recovery

- **Configuration**: Backup this deployment directory
- **Logs**: Implement log rotation and archival
- **Application State**: Consider agent/workflow state persistence

## Troubleshooting

1. **Service fails to start**:
   - Check logs: `tail -f logs/tvara.log`
   - Verify environment variables
   - Check file permissions

2. **Performance issues**:
   - Monitor resource usage: `htop`
   - Adjust worker count
   - Check network connectivity

3. **Port binding issues**:
   - Verify port is not in use: `netstat -tulpn | grep :{port}`
   - Change port in configuration if needed

## Maintenance

- **Updates**: Replace application file and restart service
- **Log Rotation**: Implement logrotate configuration
- **Monitoring**: Set up alerts for service health and performance
"""

if __name__ == "__main__":
    cli()
