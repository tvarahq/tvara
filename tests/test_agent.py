from tvara.core.agent import Agent
from tvara.core.prompt import Prompt
import pytest

def test_agent_creation():
    """Test basic agent creation with required parameters."""
    agent = Agent(
        name="TestAgent",
        model="gemini-2.5-flash",
        api_key="test_api_key"
    )
    
    assert agent.name == "TestAgent"
    assert agent.model == "gemini-2.5-flash"
    assert agent.api_key == "test_api_key"
    assert agent.max_iterations == 10  # default value

def test_agent_with_custom_prompt():
    """Test agent creation with custom prompt."""
    custom_prompt = Prompt(raw_prompt="You are a helpful assistant.")
    
    agent = Agent(
        name="CustomAgent",
        model="gemini-2.5-flash",
        api_key="test_api_key",
        prompt=custom_prompt,
        max_iterations=5
    )
    
    assert agent.name == "CustomAgent"
    assert agent.max_iterations == 5

def test_agent_validation():
    """Test that agent validates required parameters."""
    # Test missing model
    with pytest.raises(ValueError, match="Model must be specified"):
        Agent(name="Test", model="", api_key="test_key")
    
    # Test missing API key
    with pytest.raises(ValueError, match="API key must be specified"):
        Agent(name="Test", model="gemini-2.5-flash", api_key="")