from tvara.tools.base import BaseTool
from typing import Any, Dict, Optional, Union
import json
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ComposioToolWrapper(BaseTool):
    def __init__(
        self,
        composio_client,
        action_name: str,
        toolkit_name: str,
        description: str = "",
        parameters: Optional[Dict] = None,
        connected_account_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize Composio tool wrapper.

        Args:
            composio_client: Composio client instance
            action_name (str): Name of the tool action (slug)
            toolkit_name (str): Name of the toolkit
            description (str): Tool description
            parameters (Dict): Tool parameter schema
            connected_account_id (str): Composio connected account ID for this toolkit
            user_id (str): User identifier (used in standalone OAuth mode)
        """
        name = action_name.lower().replace(" ", "_").replace("-", "_")
        super().__init__(name, description or f"{toolkit_name} {action_name} action")

        self.composio_client = composio_client
        self.action_name = action_name
        self.toolkit_name = toolkit_name
        self.parameters = parameters or {}
        self.connected_account_id = connected_account_id
        self.user_id = user_id

    def get_parameters_schema(self) -> Dict:
        """Return parameter schema for this tool."""
        return self.parameters

    def run(self, input_data: Union[str, dict, Any]) -> str:
        """
        Execute the Composio tool with given input.

        Args:
            input_data: Input data for tool execution (dict preferred; str falls back to JSON parse)

        Returns:
            str: Tool execution result as string
        """
        try:
            if isinstance(input_data, dict):
                params = input_data
            elif isinstance(input_data, str):
                try:
                    params = json.loads(input_data)
                except json.JSONDecodeError:
                    params = {"input": input_data}
            else:
                params = {"input": str(input_data)}

            logger.debug("Executing %s with params: %s", self.action_name, params)

            result = self.composio_client.tools.execute(
                self.action_name,
                params,
                connected_account_id=self.connected_account_id,
                user_id=self.user_id,
                version="20260227_00"
            )

            if not result.get("successful", True):
                error = result.get("error", "Unknown error")
                logger.error("Tool %s returned error: %s", self.action_name, error)
                return f"Tool error: {error}"

            logger.debug("Tool %s completed successfully", self.action_name)
            data = result.get("data", result)
            return json.dumps(data, indent=2) if isinstance(data, dict) else str(data)

        except Exception as e:
            error_msg = str(e)
            logger.error("Tool %s execution failed: %s", self.action_name, error_msg)
            return f"Error executing {self.action_name}: {error_msg}"
