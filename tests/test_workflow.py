from tvara.core.agent import Agent
from tvara.core.workflow import Workflow
import pytest

def test_workflow_run():
    # Create agents
    agent1 = Agent(name="Agent1", goal="Process data", model="ModelA", description="First agent", tools=["Tool1"], connectors=["Connector1"])
    agent2 = Agent(name="Agent2", goal="Analyze results", model="ModelB", description="Second agent", tools=["Tool2"], connectors=["Connector2"])

    # Create a workflow with the agents
    workflow = Workflow(name="TestWorkflow", description="A test workflow for processing data", agents=[agent1, agent2])

    # Run the workflow with some input data
    input_data = "Initial input data"
    output = workflow.run(input_data)

    print(f"Workflow output: {output}")

    # Check if the output is as expected
    assert "Description: Second agent" in output
    assert "Name: Agent1" in output

def test_hierarchical_workflow_creation():
    """Test hierarchical workflow creation and validation."""
    # Create leaf agents
    worker1 = Agent(name="Worker1", model="test-model", api_key="test-key")
    worker2 = Agent(name="Worker2", model="test-model", api_key="test-key")
    
    # Create supervisor with sub-agents
    supervisor = Agent(
        name="Supervisor",
        model="test-model", 
        api_key="test-key",
        sub_agents=[worker1, worker2]
    )
    
    # Test supervisor properties
    assert supervisor.is_supervisor() == True
    assert len(supervisor.sub_agents) == 2
    assert supervisor.get_all_sub_agent_names() == ["Worker1", "Worker2"]
    assert supervisor.find_sub_agent_by_name("Worker1") == worker1
    assert supervisor.find_sub_agent_by_name("NonExistent") is None
    
    # Create hierarchical workflow
    workflow = Workflow(
        name="Test Hierarchical Workflow",
        agents=[],
        mode="hierarchical",
        manager_agent=supervisor
    )
    
    assert workflow.mode.value == "hierarchical"
    assert workflow.manager_agent == supervisor

def test_hierarchical_workflow_validation():
    """Test hierarchical workflow validation."""
    # Test without manager agent
    with pytest.raises(ValueError, match="Manager agent is required for hierarchical mode"):
        Workflow(
            name="Invalid Workflow",
            agents=[],
            mode="hierarchical"
        )
    
    # Test with manager agent that has no sub-agents
    manager_without_subs = Agent(name="Manager", model="test-model", api_key="test-key")
    with pytest.raises(ValueError, match="Manager agent must have sub-agents for hierarchical mode"):
        Workflow(
            name="Invalid Workflow",
            agents=[],
            mode="hierarchical",
            manager_agent=manager_without_subs
        )
