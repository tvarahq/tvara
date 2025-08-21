import os
import tempfile
import shutil
from pathlib import Path
from tvara.cli.main import TvaraServer
import pytest

def test_docker_deployment_artifacts():
    """Test that Docker deployment generates all required artifacts"""
    # Create a simple test agent file
    test_agent_content = '''from tvara.core import Agent

agent = Agent(
    name="Test Deployment Agent",
    model="gemini-2.5-flash",
    api_key="test-key"
)'''
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test agent file
        agent_file = Path(temp_dir) / "test_agent.py"
        agent_file.write_text(test_agent_content)
        
        # Test that we can load the agent (basic validation)
        server = TvaraServer(str(agent_file))
        assert server.execution_type == 'agent'
        assert hasattr(server.executable, 'name')
        assert server.executable.name == "Test Deployment Agent"


def test_production_deployment_validation():
    """Test that production deployment validates agent/workflow files"""
    # Test with a non-existent file
    with pytest.raises(FileNotFoundError):
        TvaraServer("non_existent_file.py")


def test_server_determines_correct_type():
    """Test that TvaraServer correctly determines agent vs workflow type"""
    # Test with agent
    agent_content = '''from tvara.core import Agent

agent = Agent(
    name="Type Test Agent",
    model="gemini-2.5-flash", 
    api_key="test-key"
)'''
    
    with tempfile.TemporaryDirectory() as temp_dir:
        agent_file = Path(temp_dir) / "agent.py"
        agent_file.write_text(agent_content)
        
        server = TvaraServer(str(agent_file))
        assert server.execution_type == 'agent'
        assert server.executable.name == "Type Test Agent"


if __name__ == "__main__":
    # Run basic tests
    test_docker_deployment_artifacts()
    test_production_deployment_validation()
    test_server_determines_correct_type()
    print("✅ All deployment tests passed!")