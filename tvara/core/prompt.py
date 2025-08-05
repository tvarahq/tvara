from typing import Optional, List
from tvara.utils.prompt_templates import template_registry
from tvara.tools import BaseTool
from tvara.connectors import BaseConnector

prerequisite = """
### VERY IMPORTANT ###

If a tool is available and relevant to the user's request, respond ONLY with this JSON:
{{
  "tool_call": {{
    "tool_name": "<tool_name>",
    "tool_input": "<tool_input>"
  }}
}}

If a connector is more suitable, respond ONLY with this JSON:
{{
  "connector_call": {{
    "connector_name": "<connector_name>",
    "connector_action": "<action>",
    "connector_input": {{
      "<key>": "<value>",
      ...
    }}
  }}
}}

Do NOT explain your actions. Do NOT include natural language.
When using `code_tool`, always return actual executable Python code.

Only if no tool or connector is relevant should you answer in natural language.
"""

class Prompt:
    def __init__(
        self,
        template_name: Optional[str] = None,
        raw_prompt: Optional[str] = None,
    ):
        if not template_name and not raw_prompt:
            raise ValueError("Either template_name or raw_prompt must be provided.")
        if template_name and raw_prompt:
            raise ValueError("Provide only one of template_name or raw_prompt, not both.")

        self.template_name = template_name
        self.raw_prompt = raw_prompt
        self.tools: List[BaseTool] = []
        self.connectors: List[BaseConnector] = []
    
    def set_tools(self, tools: List[BaseTool]):
        self.tools = tools

    def set_connectors(self, connectors: List[BaseConnector]):
        self.connectors = connectors

    def render(self) -> str:
        if self.raw_prompt:
            return self.raw_prompt + "You have access to the following tools: " + ", ".join([tool.name for tool in self.tools]) + \
                   " and the following connectors: " + ", ".join([conn.name for conn in self.connectors]) + "." + prerequisite
        template_func = template_registry.get(self.template_name)
        if not template_func:
            raise ValueError(f"Prompt template '{self.template_name}' not found.")

        return template_func(tools=self.tools, connectors=self.connectors)

