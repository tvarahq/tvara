from abc import ABC, abstractmethod
from typing import Union

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, input_data: Union[str, dict]) -> str:
        """
        Executes the tool logic on input_data and returns the result.
        """
        pass