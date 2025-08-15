from tvara.tools.base import BaseTool
from typing import Any, Dict
import json

class ComposioToolWrapper(BaseTool):
    """Simplified wrapper to make Composio tools compatible with BaseTool interface"""
    
    def __init__(self, composio_client, action_name: str, toolkit_name: str, description: str = "", parameters: Dict = None):
        name = f"{toolkit_name}_{action_name}".lower().replace(" ", "_").replace("-", "_")
        super().__init__(name, description or f"{toolkit_name} {action_name} action")
        
        self.composio_client = composio_client
        self.action_name = action_name
        self.toolkit_name = toolkit_name
        self.parameters = parameters or {}  # Store the parameters schema
    
    def get_parameters_schema(self) -> Dict:
        """Return the parameters schema for this tool"""
        return self.parameters
    
    def run(self, input_data: Any) -> str:
        """Execute the Composio tool"""
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

            print(f"Executing {self.action_name} with params: {params}")

            result = self.composio_client.tools.execute(
                slug=self.action_name,
                arguments=params,
                user_id="default"
            )

            return json.dumps(result, indent=2) if isinstance(result, dict) else str(result)

        except Exception as e:
            error_msg = str(e)
            if 'required' in error_msg.lower():
                return f"Error: Missing required parameters for {self.action_name}. Error: {error_msg}"
            elif 'invalid' in error_msg.lower():
                return f"Error: Invalid parameters for {self.action_name}. Error: {error_msg}"
            else:
                return f"Error executing {self.action_name}: {error_msg}"
