from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """
    Abstract base class for all connectors.
    """
    def __init__(self, name: str, token: str):
        self.name = name
        self.token = token

    @abstractmethod
    def run(self, action: str, input: dict) -> dict:
        pass