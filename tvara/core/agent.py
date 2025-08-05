from typing import List, Optional
from .prompt import Prompt
from tvara.models import ModelFactory
from tvara.tools import BaseTool
from tvara.connectors import BaseConnector
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
        connectors: Optional[List[BaseConnector]] = None,
    ):
        """
        Initializes a Tvara Agent.

        ## Params:
        - name (str): The name of the agent.
        - model (str): The model to use for the agent.
        - api_key (str): The API key for the model.
        - prompt (Optional[Prompt]): The prompt to use for the agent. If not provided, a default prompt will be created.
        - tools (Optional[List[BaseTool]]): A list of tools that the agent can use. If not provided, no tools will be available.
        - connectors (Optional[List[str]]): A list of connectors that the agent can use. If not provided, no connectors will be available.

        ## Raises:
        - ValueError: If the model or API key is not specified.
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
        for conn in self.connectors:
            if not isinstance(conn, BaseConnector):
                raise ValueError(f"Connector {conn} must be a subclass of BaseConnector")

        self.prompt = prompt or Prompt(
            template_name="basic_prompt_template",
        )

        self.prompt.set_tools(self.tools)
        self.prompt.set_connectors(self.connectors)

    def _extract_json(self, text: str) -> dict | None:
        try:
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            return json.loads(text)
        except Exception:
            return None

    def _use_tool(self, tool_name: str, input_data: str) -> str:
        for tool in self.tools:
            if isinstance(tool, BaseTool) and tool.name == tool_name:
                return tool.run(input_data)
        raise ValueError(f"Tool '{tool_name}' not found.")

    def _use_connector(self, connector_name: str, action: str, input_data: dict) -> str:
        for connector in self.connectors:
            if isinstance(connector, BaseConnector) and connector.name == connector_name:
                return connector.run(action, input_data)
        raise ValueError(f"Connector '{connector_name}' not found.")

    def run(self, input_data: str) -> str:
        model_instance = ModelFactory.create_model(self.model, self.api_key)

        prompt_text = self.prompt.render() + f"\n\nUser input: {input_data}"
        response = model_instance.get_response(prompt_text)

        tool_name = None
        tool_input = None
        connector_name = None
        connector_action = None
        connector_input = None
        try:
            response_json = self._extract_json(response)
            if isinstance(response_json, dict) and "tool_call" in response_json:
                tool_call = response_json["tool_call"]
                tool_name = tool_call.get("tool_name")
                tool_input = tool_call.get("tool_input")

            elif isinstance(response_json, dict) and "connector_call" in response_json:
                connector_call = response_json["connector_call"]
                connector_name = connector_call.get("connector_name")
                connector_action = connector_call.get("connector_action")
                connector_input = connector_call.get("connector_input")
        except Exception:
            pass

        if tool_name:
            try:
                tool_result = self._use_tool(tool_name, tool_input)
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
        
        elif connector_name:
            try:
                connector_result = self._use_connector(connector_name, connector_action, connector_input)
            except Exception as e:
                return f"Error using connector '{connector_name}': {str(e)}"

            followup_prompt = (
                self.prompt.render() +
                f"\n\nUser input: {input_data}\n"
                f"Connector '{connector_name}' was called with action '{connector_action}' and input '{connector_input}'.\n"
                f"Connector result: {connector_result}\n"
                "Please use this information to answer the user's question."
            )
            return model_instance.get_response(followup_prompt)

        return response
