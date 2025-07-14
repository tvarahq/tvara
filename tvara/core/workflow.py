from typing import List, Optional
from tvara.core.agent import Agent

class Workflow:
    def __init__(self, name: str, description: Optional[str] = None, agents: Optional[List[Agent]] = None, architecture: Optional[str] = None):
        """
        Initializes a new Workflow instance.

        Args:
            name (str): The name of the workflow.
            description (Optional[str]): A brief description of the workflow.
            agents (Optional[List[Agent]]): A list of agents involved in the workflow.
            architecture (Optional[str]): The architecture of the workflow.
        """
        self.name = name
        self.description = description
        self.agents = agents if agents is not None else []
        self.architecture = architecture