from typing import List, Optional
from .prompt import Prompt
from tvara.models.model_factory import ModelFactory
from tvara.tools.BaseTool import BaseTool
import json
import re

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

    def _extract_json(self, text: str) -> dict | None:
        try:
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            return json.loads(text)
        except Exception:
            return None

    def use_tool(self, tool_name: str, input_data: str) -> str:
        for tool in self.tools:
            if isinstance(tool, BaseTool) and tool.name == tool_name:
                return tool.run(input_data)
        raise ValueError(f"Tool '{tool_name}' not found.")

    def run(self, input_data: str) -> str:
        model_instance = ModelFactory.create_model(self.model, self.api_key)

        prompt_text = self.prompt.render() + f"\n\nUser input: {input_data}"
        response = model_instance.get_response(prompt_text)

        tool_name = None
        tool_input = None
        try:
            response_json = self._extract_json(response)
            if isinstance(response_json, dict) and "tool_call" in response_json:
                tool_call = response_json["tool_call"]
                tool_name = tool_call.get("tool_name")
                tool_input = tool_call.get("tool_input")
        except Exception:
            pass

        if tool_name:
            try:
                tool_result = self.use_tool(tool_name, tool_input)
            except Exception as e:
                return f"Error using tool '{tool_name}': {str(e)}"

            followup_prompt = (
                self.prompt.render() +
                f"\n\nUser input: {input_data}\n"
                f"Tool '{tool_name}' was called with input '{tool_input}'.\n"
                f"Tool result: {tool_result}\n"
                "Please use this information to answer the user's question."
            )
            return model_instance.get_response(followup_prompt)

        return response
