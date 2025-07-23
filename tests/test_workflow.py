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
