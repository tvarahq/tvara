from typing import Optional, List
from tvara.utils.prompt_templates import template_registry
from tvara.tools import BaseTool

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
        return self.raw_prompt
