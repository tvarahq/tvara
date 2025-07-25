from typing import List, Optional, Dict, Union
from tvara.core.prompt import Prompt
from tvara.models.model_factory import ModelFactory

class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        api_key: str,
        prompt: Optional[Prompt] = None,
        tools: Optional[List[str]] = None,
        connectors: Optional[List[str]] = None,
    ):
        if not model:
            raise ValueError("Model must be specified.")
        if not api_key:
            raise ValueError("API key must be specified.")

        self.name = name
        self.model = model
        self.api_key = api_key
        self.tools = tools or []
        self.connectors = connectors or []

        self.prompt = prompt or Prompt(
            template_name="basic_prompt_template",
            variables={"name": self.name, "description": "An AI assistant."},
            tools=self.tools,
            connectors=self.connectors
        )

    def run(self, input_data: str) -> str:
        model_instance = ModelFactory.create_model(self.model, self.api_key)
        prompt_text = self.prompt.render() + f"\n\nUser input: {input_data}"
        return model_instance.get_response(prompt_text)
