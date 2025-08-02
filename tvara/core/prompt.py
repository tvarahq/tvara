from typing import Optional, Dict, List, Union
from tvara.utils.prompt_templates import template_registry
from tvara.tools import BaseTool
from tvara.connectors import BaseConnector

class Prompt:
    def __init__(
        self,
        template_name: Optional[str] = None,
        variables: Optional[Dict[str, Union[str, List[str]]]] = None,
        raw_prompt: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        connectors: Optional[List[BaseConnector]] = None,
    ):
        if not template_name and not raw_prompt:
            raise ValueError("Either template_name or raw_prompt must be provided.")
        if template_name and raw_prompt:
            raise ValueError("Provide only one of template_name or raw_prompt, not both.")

        self.template_name = template_name
        self.variables = variables or {}
        self.raw_prompt = raw_prompt
        self.tools = tools or []
        self.connectors = connectors or []

    def render(self) -> str:
        if self.raw_prompt:
            return self.raw_prompt + " Tools available: " + ", ".join(tool.name for tool in self.tools) + " Connectors available: " + ", ".join(connector.name for connector in self.connectors)
        template_func = template_registry.get(self.template_name)
        if not template_func:
            raise ValueError(f"Prompt template '{self.template_name}' not found.")

        return template_func(**self.variables, tools=self.tools, connectors=self.connectors)
