from tvara.tools.base import BaseTool
from typing import Any, Dict
import json
import logging

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

class ComposioToolWrapper(BaseTool):
    def __init__(self, composio_client, action_name: str, toolkit_name: str, description: str = "", parameters: Dict = None):
        """
        Initialize Composio tool wrapper.
        
        Args:
            composio_client: Composio client instance
            action_name (str): Name of the tool action
            toolkit_name (str): Name of the toolkit
            description (str): Tool description
            parameters (Dict): Tool parameter schema
        """
        name = f"{toolkit_name}_{action_name}".lower().replace(" ", "_").replace("-", "_")
        super().__init__(name, description or f"{toolkit_name} {action_name} action")
        
        self.composio_client = composio_client
        self.action_name = action_name
        self.toolkit_name = toolkit_name
        self.parameters = parameters or {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Tool-{name}")
    
    def _log(self, message: str, level: str = "info"):
        """
        Log message with specified level and print to console.
        
        Args:
            message (str): Message to log
            level (str): Logging level
        """
        print(message)
        getattr(self.logger, level)(message)
    
    def get_parameters_schema(self) -> Dict:
        """
        Get parameter schema for this tool.
        
        Returns:
            Dict: Parameter schema dictionary
        """
        return self.parameters
    
    def run(self, input_data: Any) -> str:
        """
        Execute the Composio tool with given input.
        
        Args:
            input_data (Any): Input data for tool execution
            
        Returns:
            str: Tool execution result as string
        """
        try:
            if isinstance(input_data, str):
                try:
                    params = json.loads(input_data)
                except json.JSONDecodeError:
                    if 'email' in self.action_name.lower():
                        if 'send' in self.action_name.lower():
                            params = {
                                "recipient_email": input_data,
                                "subject": "Message from AI Assistant",
                                "body": input_data
                            }
                        elif 'fetch' in self.action_name.lower() or 'list' in self.action_name.lower():
                            params = {"query": input_data}
                        else:
                            params = {"input": input_data}
                    else:
                        params = {"query": input_data}
            elif isinstance(input_data, dict):
                params = input_data
            else:
                params = {"input": str(input_data)}

            self._log(f"{CYAN}   🔧 Executing {self.action_name} with params: {params}{RESET}")

            result = self.composio_client.tools.execute(
                slug=self.action_name,
                arguments=params,
                user_id="default"
            )

            self._log(f"{GREEN}   ✅ Tool execution completed successfully{RESET}")
            return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)

        except Exception as e:
            error_msg = str(e)
            self._log(f"{RED}   ❌ Tool execution failed: {error_msg}{RESET}", "error")
            
            if 'required' in error_msg.lower():
                return f"Error: Missing required parameters for {self.action_name}. Error: {error_msg}"
            elif 'invalid' in error_msg.lower():
                return f"Error: Invalid parameters for {self.action_name}. Error: {error_msg}"
            else:
                return f"Error executing {self.action_name}: {error_msg}"
