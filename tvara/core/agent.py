from typing import List, Optional, Dict, Any
from .prompt import Prompt
from tvara.models import ModelFactory
from tvara.tools.ComposioTool import ComposioToolWrapper
import json
import re

BLUE = "\033[94m"
RESET = "\033[0m"

class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        api_key: str,
        composio_api_key: str,
        composio_toolkits: List[str],
        prompt: Optional[Prompt] = None,
        max_iterations: int = 10,
        user_id: str = "default"
    ):
        if not model:
            raise ValueError("Model must be specified.")
        if not api_key:
            raise ValueError("API key must be specified.")
        if not composio_api_key:
            raise ValueError("Composio API key must be specified.")
        if not composio_toolkits:
            raise ValueError("At least one Composio toolkit must be specified.")

        self.name = name
        self.model = model
        self.api_key = api_key
        self.max_iterations = max_iterations
        self.user_id = user_id
        
        self.composio_client = self._initialize_composio_client(composio_api_key)
        
        self.tools = self._setup_toolkits(composio_toolkits)

        self.prompt = prompt or Prompt(template_name="agent_prompt_template")
        self.prompt.set_tools(self.tools)

    def _initialize_composio_client(self, api_key: str):
        """Initialize Composio client"""
        try:
            from composio import Composio
            client = Composio(api_key=api_key)
            print("Composio client initialized successfully")
            return client
        except ImportError:
            raise ImportError("Composio package not installed. Install with: pip install composio==0.8.0")
        except Exception as e:
            raise Exception(f"Composio initialization failed: {e}")

    def _setup_toolkits(self, toolkits: List[str]) -> List[ComposioToolWrapper]:
        """Setup toolkits with authorization and return wrapped tools"""
        all_tools = []
        
        for toolkit in toolkits:
            print(f"🔑 Setting up {toolkit}...")
            
            try:
                connection_request = self.composio_client.toolkits.authorize(
                    user_id=self.user_id, 
                    toolkit=toolkit.lower()
                )
                
                print(f"🔗 Visit the URL to authorize {toolkit}:")
                print(f"👉 {connection_request.redirect_url}")
                print("⏳ Waiting for authorization...")
                
                connection_request.wait_for_connection()
                print(f"✅ {toolkit} authorized successfully!")
                
            except Exception as e:
                if 'already authorized' in str(e).lower():
                    print(f"✅ {toolkit} was already authorized")
                else:
                    print(f"❌ Authorization failed for {toolkit}: {e}")
                    continue
            
            try:
                toolkit_tools = self.composio_client.tools.get(
                    user_id=self.user_id,
                    toolkits=[toolkit.upper()]
                )
                
                print(f"📦 Found {len(toolkit_tools) if toolkit_tools else 0} tools for {toolkit}")
                
                if toolkit_tools:
                    for tool in toolkit_tools:
                        try:
                            if isinstance(tool, dict) and 'function' in tool:
                                function_info = tool['function']
                                slug = function_info.get('name')
                                description = function_info.get('description', '')
                                parameters = function_info.get('parameters', {})
                            else:
                                slug = tool.get('slug') or tool.get('name')
                                description = tool.get('description', '')
                                parameters = tool.get('parameters', {})

                            if not slug:
                                print(f"  ✗ Skipping tool with no slug: {tool}")
                                continue
                            
                            # Pass parameters to the wrapper
                            wrapped_tool = ComposioToolWrapper(
                                composio_client=self.composio_client,
                                action_name=slug,
                                toolkit_name=toolkit,
                                description=description,
                                parameters=parameters  # Include parameters schema
                            )
                            all_tools.append(wrapped_tool)
                            print(f"  ✓ Added: {slug} with parameters: {json.dumps(parameters, indent=2) if parameters else 'None'}")
                            
                        except Exception as e:
                            print(f"  ✗ Failed to wrap tool {tool}: {e}")
                            
            except Exception as e:
                print(f"❌ Failed to get tools for {toolkit}: {e}")
        
        print(f"🛠️  Total tools loaded: {len(all_tools)}")
        return all_tools

    def _extract_json(self, text: str) -> dict | None:
        """Extract JSON from model response"""
        try:
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            return json.loads(text)
        except Exception:
            return None

    def _execute_tool(self, tool_name: str, tool_input: Any) -> str:
        """Execute a tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.run(tool_input)
        
        for tool in self.tools:
            if tool_name.lower() in tool.name.lower() or tool.name.lower() in tool_name.lower():
                print(f"Using partial match: {tool.name} for requested {tool_name}")
                return tool.run(tool_input)
                
        available_tools = [tool.name for tool in self.tools]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available_tools}")

    def run(self, input_data: str) -> str:
        """Enhanced run method with iterative execution loop"""
        if not self.tools:
            return "No tools available. Please check your Composio API key and toolkit configuration."
            
        model_instance = ModelFactory.create_model(self.model, self.api_key)
        
        conversation_history = [f"User input: {input_data}"]
        
        for iteration in range(self.max_iterations):            
            current_prompt = self._build_prompt_with_history(conversation_history)
            
            response = model_instance.get_response(current_prompt)            
            tool_call = self._extract_tool_call(response)
            
            if not tool_call:
                if "tool failed" in response.lower() or "error executing tool" in response.lower():
                    conversation_history.append(f"Assistant response without tool call: {response}")
                    continue
                else:
                    return response
            try:
                tool_result = self._execute_tool(
                    tool_call["tool_name"], 
                    tool_call["tool_input"]
                )
                                
                conversation_history.append(
                    f"Assistant called tool '{tool_call['tool_name']}' with input: {tool_call['tool_input']}"
                )
                conversation_history.append(f"Tool result: {tool_result}")
                
            except Exception as e:
                error_msg = f"Error executing tool '{tool_call['tool_name']}': {str(e)}"
                print(error_msg)
                conversation_history.append(error_msg)

        return "Maximum iterations reached. Please try rephrasing your request."

    def _build_prompt_with_history(self, history: List[str]) -> str:
        """Build prompt including conversation history"""
        base_prompt = self.prompt.render()
        history_text = "\n".join(history)
        return f"{base_prompt}\n\nConversation:\n{history_text}\n\nPlease respond:"

    def _extract_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract tool call from model response"""
        try:
            response_json = self._extract_json(response)
            if isinstance(response_json, dict) and "tool_call" in response_json:
                return response_json["tool_call"]
        except Exception:
            pass
        return None
