from typing import List, Optional, Dict, Any
from .prompt import Prompt
from tvara.models import ModelFactory
from tvara.tools.ComposioTool import ComposioToolWrapper
import json
import re
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("composio").setLevel(logging.WARNING)

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
RESET = "\033[0m"

class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        api_key: str,
        composio_api_key: Optional[str] = None,
        composio_toolkits: Optional[List[str]] = None,
        prompt: Optional[Prompt] = None,
        max_iterations: int = 10,
        user_id: str = "default"
    ):
        """
        Initialize an AI Agent.
        
        Args:
            name (str): Agent identifier name
            model (str): LLM model name to use
            api_key (str): API key for the LLM model
            composio_api_key (Optional[str]): API key for Composio tools integration
            composio_toolkits (Optional[List[str]]): List of Composio toolkit names to enable
            prompt (Optional[Prompt]): Custom prompt template
            max_iterations (int): Maximum tool usage iterations
            user_id (str): User identifier for tool authorization
            
        Raises:
            ValueError: If required parameters are missing
        """
        if not model:
            raise ValueError("Model must be specified.")
        if not api_key:
            raise ValueError("API key must be specified.")

        self.name = name
        self.model = model
        self.api_key = api_key
        self.max_iterations = max_iterations
        self.user_id = user_id
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"Agent-{name}")
        self.logger.setLevel(logging.WARNING) 
        
        self.tools = []
        self.composio_client = None
        
        self._log(f"{BOLD}{CYAN}🤖 Initializing Agent: {name}{RESET}")
        self._log(f"{BLUE}   Model: {model}{RESET}")
        
        if composio_api_key and composio_toolkits:
            self.composio_client = self._initialize_composio_client(composio_api_key)
            self.tools = self._setup_toolkits(composio_toolkits)
            self._log(f"{GREEN}✅ Composio integration enabled with {len(self.tools)} tools{RESET}")
        else:
            self._log(f"{YELLOW}⚡ Running in basic mode (no external tools){RESET}")

        self.prompt = prompt or Prompt(template_name="agent_prompt_template")
        self.prompt.set_tools(self.tools)
        self._log(f"{GREEN}✅ Agent '{name}' initialized successfully{RESET}\n")

    def _log(self, message: str, level: str = "info"):
        """
        Log a message with specified level.
        
        Args:
            message (str): Message to log
            level (str): Logging level (info, warning, error)
        """
        print(message)
        if hasattr(self, 'logger'):
            getattr(self.logger, level)(message)

    def _initialize_composio_client(self, api_key: Optional[str]):
        """
        Initialize Composio client for tool integration.
        
        Args:
            api_key (Optional[str]): Composio API key
            
        Returns:
            Composio client instance or None
            
        Raises:
            ImportError: If Composio package not installed
            Exception: If initialization fails
        """
        if not api_key:
            return None

        try:
            from composio import Composio
            client = Composio(api_key=api_key)
            self._log(f"{GREEN}   ✓ Composio client connected{RESET}")
            return client
        except ImportError:
            raise ImportError("Composio package not installed. Install with: pip install composio==0.8.0")
        except Exception as e:
            raise Exception(f"Composio initialization failed: {e}")
        
    def _is_no_auth_toolkit(self, toolkit: str) -> bool:
        """
        Check if toolkit requires authentication.
        
        Args:
            toolkit (str): Toolkit name to check
            
        Returns:
            bool: True if no authentication required
        """
        no_auth_toolkits = [
            "COMPOSIO_SEARCH", 
            "CODEINTERPRETER", 
            "ENTELLIGENCE",
            "HACKERNEWS",
            "TEXT_TO_PDF",
            "WEATHERMAP"
        ]
        return toolkit.upper() in no_auth_toolkits

    def _setup_toolkits(self, toolkits: Optional[List[str]]) -> List[ComposioToolWrapper]:
        """
        Setup and authorize Composio toolkits.
        
        Args:
            toolkits (Optional[List[str]]): List of toolkit names to setup
            
        Returns:
            List[ComposioToolWrapper]: List of wrapped tool instances
        """
        if not toolkits:
            return []
        
        all_tools = []
        self._log(f"{CYAN}   🔧 Setting up toolkits...{RESET}")
        
        for toolkit in toolkits:
            self._log(f"{BLUE}   📦 {toolkit}:{RESET}")

            if not self._is_no_auth_toolkit(toolkit):
                try:
                    connection_request = self.composio_client.toolkits.authorize(
                        user_id=self.user_id, 
                        toolkit=toolkit.lower()
                    )
                    
                    self._log(f"{YELLOW}Auth required{RESET}")
                    self._log(f"{CYAN}      🔗 Visit: {connection_request.redirect_url}{RESET}")
                    self._log(f"{YELLOW}      ⏳ Waiting for authorization...{RESET}")
                    
                    connection_request.wait_for_connection()
                    self._log(f"{GREEN}      ✅ Authorized{RESET}")
                    
                except Exception as e:
                    if 'already authorized' in str(e).lower():
                        self._log(f"{GREEN}Already authorized{RESET}")
                    else:
                        self._log(f"{RED}❌ Failed: {e}{RESET}", "error")
                        continue
            else:
                self._log(f"{GREEN}Ready (no auth required){RESET}")
            
            try:
                toolkit_tools = self.composio_client.tools.get(
                    user_id=self.user_id,
                    toolkits=[toolkit.upper()]
                )
                
                tool_count = len(toolkit_tools) if toolkit_tools else 0
                self._log(f"{BLUE}      📋 Found {tool_count} tools{RESET}")
                
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
                                continue
                            
                            wrapped_tool = ComposioToolWrapper(
                                composio_client=self.composio_client,
                                action_name=slug,
                                toolkit_name=toolkit,
                                description=description,
                                parameters=parameters
                            )
                            all_tools.append(wrapped_tool)
                            
                        except Exception as e:
                            self._log(f"{RED}      ❌ Tool setup failed: {e}{RESET}", "error")
                            
            except Exception as e:
                self._log(f"{RED}      ❌ Toolkit setup failed: {e}{RESET}", "error")
        
        return all_tools

    def _extract_json(self, text: str) -> dict | None:
        """
        Extract JSON object from text response.
        
        Args:
            text (str): Text containing JSON
            
        Returns:
            dict | None: Extracted JSON object or None if not found
        """
        try:
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception:
            return None

    def _execute_tool(self, tool_name: str, tool_input: Any) -> str:
        """
        Execute a tool by name with given input.
        
        Args:
            tool_name (str): Name of tool to execute
            tool_input (Any): Input data for the tool
            
        Returns:
            str: Tool execution result
            
        Raises:
            ValueError: If tool not found
        """
        self._log(f"{CYAN}🔧 Executing tool: {tool_name}{RESET}")
        
        for tool in self.tools:
            if tool.name == tool_name:
                result = tool.run(tool_input)
                self._log(f"{GREEN}✅ Tool completed successfully{RESET}")
                return result
        
        for tool in self.tools:
            if tool_name.lower() in tool.name.lower() or tool.name.lower() in tool_name.lower():
                self._log(f"{YELLOW}🔄 Using partial match: {tool.name}{RESET}")
                result = tool.run(tool_input)
                self._log(f"{GREEN}✅ Tool completed successfully{RESET}")
                return result
                
        available_tools = [tool.name for tool in self.tools]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available_tools}")

    def run(self, input_data: str) -> str:
        """
        Process user input and generate response using tools if needed.
        
        Args:
            input_data (str): User input to process
            
        Returns:
            str: Generated response
        """
        self._log(f"\n{BOLD}{PURPLE}🚀 Agent '{self.name}' Processing Request{RESET}")
        self._log(f"{BLUE}📝 Input: {input_data[:100]}{'...' if len(input_data) > 100 else ''}{RESET}")
        
        model_instance = ModelFactory.create_model(self.model, self.api_key)
        
        if not self.tools:
            self._log(f"{YELLOW}⚡ Basic mode - responding directly{RESET}")
            current_prompt = self._build_basic_prompt(input_data)
            response = model_instance.get_response(current_prompt)
            self._print_final_response(response)
            return response
        
        conversation_history = [f"User input: {input_data}"]
        
        for iteration in range(self.max_iterations):
            self._log(f"\n{CYAN}🔄 Iteration {iteration + 1}/{self.max_iterations}{RESET}")
            
            current_prompt = self._build_prompt_with_history(conversation_history)
            response = model_instance.get_response(current_prompt)
            
            tool_call = self._extract_tool_call(response)
            
            if not tool_call:
                if "tool failed" in response.lower() or "error executing tool" in response.lower():
                    self._log(f"{RED}⚠️  Tool execution failed, continuing...{RESET}", "warning")
                    conversation_history.append(f"Assistant response without tool call: {response}")
                    continue
                else:
                    self._log(f"{GREEN}✅ Final response ready{RESET}")
                    self._print_final_response(response)
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
                self._log(f"{RED}❌ {error_msg}{RESET}", "error")
                conversation_history.append(error_msg)

        final_response = "Maximum iterations reached. Please try rephrasing your request."
        self._log(f"{RED}⏰ {final_response}{RESET}", "warning")
        return final_response

    def _print_final_response(self, response: str):
        """
        Print final response with formatting.
        
        Args:
            response (str): Response to print
        """
        self._log(f"\n{BOLD}{GREEN}{'='*60}{RESET}")
        self._log(f"{BOLD}{GREEN}🎯 FINAL RESPONSE FROM {self.name.upper()}{RESET}")
        self._log(f"{BOLD}{GREEN}{'='*60}{RESET}")
        self._log(f"{WHITE}{response}{RESET}")
        self._log(f"{BOLD}{GREEN}{'='*60}{RESET}\n")

    def _build_prompt_with_history(self, history: List[str]) -> str:
        """
        Build prompt including conversation history.
        
        Args:
            history (List[str]): List of conversation messages
            
        Returns:
            str: Complete prompt with history
        """
        base_prompt = self.prompt.render()
        history_text = "\n".join(history)
        return f"{base_prompt}\n\nConversation:\n{history_text}\n\nPlease respond:"
    
    def _build_basic_prompt(self, input_data: str) -> str:
        """
        Build basic prompt for agents without tools.
        
        Args:
            input_data (str): User input
            
        Returns:
            str: Basic prompt template
        """
        return f"""You are an AI assistant that listens carefully to the user's input and provides a thoughtful response.

User input: {input_data}

Please provide a helpful and informative response to the user's question or request."""

    def _extract_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extract tool call from model response.
        
        Args:
            response (str): Model response text
            
        Returns:
            Optional[Dict[str, Any]]: Tool call dict or None if not found
        """
        try:
            response_json = self._extract_json(response)
            if isinstance(response_json, dict) and "tool_call" in response_json:
                return response_json["tool_call"]
        except Exception:
            pass
        return None
