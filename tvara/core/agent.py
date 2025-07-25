from typing import List, Optional
from tvara.core import Prompt
from tvara.models.model_factory import ModelFactory
from tvara.tools.BaseTool import BaseTool

class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        api_key: str,
        prompt: Optional[Prompt] = None,
        tools: Optional[List[BaseTool]] = None,
        connectors: Optional[List[str]] = None,
    ):
        """
        Initialize a new Agent instance.

        Args:
            name (str): The name of the agent.
            model (str): The model to use for the agent.
            api_key (str): The API key for the model.
            prompt (Optional[Prompt]): A custom prompt for the agent.
            tools (Optional[List[BaseTool]]): A list of tool instances to be used by the agent.
            connectors (Optional[List[str]]): A list of connectors to be used by the agent.

        Raises:
            ValueError: If the model is not specified or the API key is not provided.
        """
        if not model:
            raise ValueError("Model must be specified.")
        if not api_key:
            raise ValueError("API key must be specified.")

        self.name = name
        self.model = model
        self.api_key = api_key
        
        self.tools = tools or []
        for tool in self.tools:
            if not isinstance(tool, BaseTool):
                raise ValueError(f"Tool {tool} must be a subclass of BaseTool")
        
        self.connectors = connectors or []

        self.prompt = prompt or Prompt(
            template_name="basic_prompt_template",
            variables={"name": self.name, "description": "An AI assistant."},
            tools=self.tools,
            connectors=self.connectors
        )

    def use_tool(self, tool_name: str, input_data: str) -> str:
        for tool in self.tools:
            if isinstance(tool, BaseTool) and tool.name == tool_name:
                return tool.run(input_data)
        raise ValueError(f"Tool '{tool_name}' not found in agent.")


    def run(self, input_data: str) -> str:
        model_instance = ModelFactory.create_model(self.model, self.api_key)
        prompt_text = self.prompt.render() + f"\n\nUser input: {input_data}"
        return model_instance.get_response(prompt_text)
