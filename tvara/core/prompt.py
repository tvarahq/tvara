from typing import Optional, List
from tvara.utils.prompt_templates import template_registry
from tvara.tools import BaseTool
import json

prerequisite = """
### VERY IMPORTANT ###

When using tools, you MUST use the exact parameter names and structure as specified in the tool's Parameters Schema.

If a tool is available and relevant to the user's request, respond ONLY with this JSON:
{
  "tool_call": {
    "tool_name": "<exact_tool_name>",
    "tool_input": {
      // Use the exact parameter names and types from the tool's parameters schema
    }
  }
}

Do NOT explain your actions. Do NOT include natural language.
When using `code_tool`, always return actual executable Python code.

Only if no tool is relevant should you answer in natural language.
"""

class Prompt:
    def __init__(
        self,
        template_name: Optional[str] = None,
        raw_prompt: Optional[str] = None,
    ):
        """
        Initialize a prompt with either template or raw content.
        
        Args:
            template_name (Optional[str]): Name of predefined template
            raw_prompt (Optional[str]): Custom raw prompt text
            
        Raises:
            ValueError: If neither or both parameters provided
        """
        if not template_name and not raw_prompt:
            raise ValueError("Either template_name or raw_prompt must be provided.")
        if template_name and raw_prompt:
            raise ValueError("Provide only one of template_name or raw_prompt, not both.")

        self.template_name = template_name
        self.raw_prompt = raw_prompt
        self.tools: List[BaseTool] = []
    
    def set_tools(self, tools: List[BaseTool]):
        """
        Set available tools for the prompt.
        
        Args:
            tools (List[BaseTool]): List of available tools
        """
        self.tools = tools

    def render(self) -> str:
        """
        Render the complete prompt with tools information.
        
        Returns:
            str: Complete rendered prompt
        """
        if self.raw_prompt:
            return self._render_raw_prompt()
        
        template_func = template_registry.get(self.template_name)
        if not template_func:
            raise ValueError(f"Prompt template '{self.template_name}' not found.")

        return template_func(tools=self.tools)
    
    def _render_raw_prompt(self) -> str:
        """
        Render raw prompt with enhanced tool information.
        
        Returns:
            str: Raw prompt with tool details
        """
        if not self.tools:
            return self.raw_prompt + "\n\nNo tools available."
        
        tools_info = []
        for tool in self.tools:
            params_schema = tool.get_parameters_schema() if hasattr(tool, 'get_parameters_schema') else {}
            tool_info = f"""
Tool: {tool.name}
Description: {tool.description}
Parameters Schema: {json.dumps(params_schema, indent=2) if params_schema else 'No specific parameters required'}
"""
            tools_info.append(tool_info)
        
        tools_section = f"""

You have access to the following tools with their parameter schemas:
{"".join(tools_info)}
"""
        
        return self.raw_prompt + tools_section + "\n" + prerequisite
