from typing import List, Optional
class Agent:
    """
    Initializes a new Agent instance.
    Args:
        name (str): The name of the agent.
        goal (str): The primary goal of the agent.
        model (str): The model used by the agent.
        description (Optional[str]): A brief description of the agent.
        tools (Optional[List[str]]): A list of tools available to the agent.
        connectors (Optional[List[str]]): A list of connectors used by the agent.
    """
    def __init__(self, name: str, goal: str, model: str, description: Optional[str] = None, tools: Optional[List[str]] = None, connectors: Optional[List[str]] = None):
        self.name = name
        self.goal = goal
        self.model = model
        self.tools = tools if tools is not None else []
        self.connectors = connectors if connectors is not None else []
        self.description = description

        