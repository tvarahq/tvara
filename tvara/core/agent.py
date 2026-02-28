from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional

from .prompt import Prompt
from tvara.models import ModelFactory
from tvara.tools.ComposioTool import ComposioToolWrapper
from tvara.tools.CustomTool import CustomToolWrapper
from tvara.utils.auth_cache import AuthCache

# Silence noisy third-party loggers unconditionally — they have their own
# handlers and will otherwise double-print even when verbose=True.
for _noisy in ("httpx", "composio", "urllib3", "openai", "anthropic", "google"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
    logging.getLogger(_noisy).propagate = False

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to external tools. "
    "When the user asks you to perform an action or retrieve information, "
    "always use the available tools rather than saying you cannot do it."
)


@dataclass
class RunResult:
    """Structured result returned by Agent.run() / Agent.run_sync()."""
    output: str
    stop_reason: Literal["stop", "max_iterations", "error"]
    tool_calls: List[Dict] = field(default_factory=list)
    usage: Optional[Dict] = None


class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        api_key: str,
        composio_api_key: Optional[str] = None,
        composio_toolkits: Optional[List[str]] = None,
        connected_accounts: Optional[Dict[str, str]] = None,
        custom_tools: Optional[List[Any]] = None,
        prompt: Optional[Prompt] = None,
        max_iterations: int = 10,
        user_id: str = "default",
        cache_auth: bool = True,
        cache_validity_minutes: int = 10,
        verbose: bool = False,
    ):
        """
        Initialize an AI Agent with optional tool integration and auth caching.

        Args:
            name: Agent identifier name
            model: LLM model name to use
            api_key: API key for the LLM model
            composio_api_key: API key for Composio tools integration
            composio_toolkits: List of Composio toolkit names to enable
            connected_accounts: Dict mapping toolkit_slug -> connected_account_id
            custom_tools: List of CustomToolWrapper instances
            prompt: Custom prompt template
            max_iterations: Maximum tool usage iterations
            user_id: User identifier for tool authorization
            cache_auth: Enable authentication caching
            cache_validity_minutes: Cache validity in minutes
            verbose: Print debug logs to stdout when True (default False)
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

        # verbose=True attaches a StreamHandler to the tvara logger so debug
        # output appears without the caller needing to configure logging.
        # propagate=False keeps records inside our handler and prevents
        # third-party root-logger handlers from printing duplicates.
        if verbose:
            _tvara_logger = logging.getLogger("tvara")
            if not any(isinstance(h, logging.StreamHandler) for h in _tvara_logger.handlers):
                _handler = logging.StreamHandler()
                _handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
                _tvara_logger.addHandler(_handler)
            _tvara_logger.setLevel(logging.INFO)
            _tvara_logger.propagate = False

        self.auth_cache = AuthCache(cache_validity_minutes=cache_validity_minutes) if cache_auth else None
        self.tools: List[Any] = []
        self.composio_client = None

        logger.info("Initializing Agent: %s (model=%s)", name, model)

        # Instantiate the model once — avoids creating a new HTTP client per call.
        self._model_instance = ModelFactory.create_model(model, api_key)

        if composio_api_key and connected_accounts:
            self.composio_client = self._initialize_composio_client(composio_api_key)
            self.tools = self._setup_toolkits_from_accounts(connected_accounts)
            logger.info("Composio integration enabled with %d tools", len(self.tools))
        elif composio_api_key and composio_toolkits:
            self.composio_client = self._initialize_composio_client(composio_api_key)
            self.tools = self._setup_toolkits(composio_toolkits)
            logger.info("Composio integration enabled with %d tools", len(self.tools))

        if custom_tools:
            for tool in custom_tools:
                if isinstance(tool, CustomToolWrapper):
                    self.tools.append(tool)
                else:
                    raise ValueError("Custom tools must be instances of CustomToolWrapper")
            logger.info("Added %d custom tools", len(custom_tools))

        if not self.tools:
            logger.info("Agent '%s' running in basic mode (no external tools)", name)

        self.prompt = prompt or Prompt(template_name="agent_prompt_template")
        self.prompt.set_tools(self.tools)
        logger.info("Agent '%s' initialized successfully", name)

    # ------------------------------------------------------------------
    # Composio setup helpers
    # ------------------------------------------------------------------

    def _initialize_composio_client(self, api_key: Optional[str]):
        """Initialize Composio client for tool integration."""
        if not api_key:
            return None
        try:
            from composio import Composio
            client = Composio(api_key=api_key)
            logger.debug("Composio client connected")
            return client
        except ImportError:
            raise ImportError(
                "Composio package not installed. Install with: pip install composio==0.8.0"
            )
        except Exception as e:
            raise Exception(f"Composio initialization failed: {e}")

    def _setup_toolkits_from_accounts(self, connected_accounts: Dict[str, str]) -> List[ComposioToolWrapper]:
        """
        Backend mode: fetch tool schemas for pre-authenticated connections.
        Skips OAuth entirely — uses connected_account_id for execution.
        """
        all_tools: List[ComposioToolWrapper] = []
        toolkit_slugs = list(connected_accounts.keys())
        logger.info("Loading tools for toolkits: %s", toolkit_slugs)

        try:
            raw_tools = self.composio_client.tools.get_raw_composio_tools(
                toolkits=[s.upper() for s in toolkit_slugs]
            )
        except Exception as e:
            logger.error("Failed to fetch tool schemas: %s", e)
            return []

        logger.debug("Found %d tools", len(raw_tools))

        for tool in raw_tools:
            try:
                slug = tool.slug
                toolkit_key = tool.toolkit.slug.lower()
                connected_account_id = connected_accounts.get(toolkit_key)
                description = getattr(tool, "description", "")
                parameters: Dict = {}
                if hasattr(tool, "input_parameters") and tool.input_parameters:
                    params_obj = tool.input_parameters
                    if hasattr(params_obj, "model_dump"):
                        parameters = params_obj.model_dump()
                    elif hasattr(params_obj, "dict"):
                        parameters = params_obj.dict()
                    elif isinstance(params_obj, dict):
                        parameters = params_obj

                wrapped = ComposioToolWrapper(
                    composio_client=self.composio_client,
                    action_name=slug,
                    toolkit_name=toolkit_key,
                    description=description,
                    parameters=parameters,
                    connected_account_id=connected_account_id,
                )
                all_tools.append(wrapped)
            except Exception as e:
                logger.error("Tool setup failed for %s: %s", getattr(tool, "slug", "?"), e)

        return all_tools

    def _has_active_connection(self, toolkit: str) -> bool:
        """Check if user already has an active Composio connection for this toolkit."""
        try:
            connections = self.composio_client.connected_accounts.list(user_id=self.user_id)
            for conn in connections:
                status = getattr(conn, "status", "") or ""
                app = (
                    getattr(conn, "app_name", "")
                    or getattr(conn, "toolkit_slug", "")
                    or ""
                )
                if status.upper() == "ACTIVE" and toolkit.lower() in app.lower():
                    return True
        except Exception:
            pass
        return False

    def _is_no_auth_toolkit(self, toolkit: str) -> bool:
        """Check if toolkit requires authentication."""
        no_auth_toolkits = {
            "COMPOSIO_SEARCH",
            "CODEINTERPRETER",
            "ENTELLIGENCE",
            "HACKERNEWS",
            "TEXT_TO_PDF",
            "WEATHERMAP",
        }
        return toolkit.upper() in no_auth_toolkits

    def _setup_toolkits(self, toolkits: Optional[List[str]]) -> List[ComposioToolWrapper]:
        """Setup and authorize Composio toolkits with smart caching."""
        if not toolkits:
            return []

        all_tools: List[ComposioToolWrapper] = []
        logger.info("Setting up toolkits: %s", toolkits)

        for toolkit in toolkits:
            if not self._is_no_auth_toolkit(toolkit):
                if self.auth_cache and self.auth_cache.is_toolkit_cached(toolkit, self.user_id):
                    logger.debug("Using cached auth for %s", toolkit)
                elif self._has_active_connection(toolkit):
                    logger.debug("Active connection found for %s, skipping OAuth", toolkit)
                    if self.auth_cache:
                        self.auth_cache.cache_toolkit_auth(toolkit, self.user_id)
                else:
                    try:
                        connection_request = self.composio_client.toolkits.authorize(
                            user_id=self.user_id,
                            toolkit=toolkit.lower(),
                        )
                        print(
                            f"[tvara] Auth required for {toolkit} — visit: {connection_request.redirect_url}",
                            flush=True,
                        )
                        logger.info(
                            "Auth required for %s — visit: %s",
                            toolkit,
                            connection_request.redirect_url,
                        )
                        connection_request.wait_for_connection()
                        logger.info("Authorized %s", toolkit)

                        if self.auth_cache:
                            self.auth_cache.cache_toolkit_auth(toolkit, self.user_id)
                    except Exception as e:
                        if "already authorized" in str(e).lower():
                            logger.debug("Already authorized: %s", toolkit)
                            if self.auth_cache:
                                self.auth_cache.cache_toolkit_auth(toolkit, self.user_id)
                        else:
                            logger.error("Failed to authorize %s: %s", toolkit, e)
                            continue
            else:
                logger.debug("Toolkit %s requires no auth", toolkit)

            try:
                toolkit_tools = self.composio_client.tools.get(
                    user_id=self.user_id,
                    toolkits=[toolkit.upper()],
                )
                tool_count = len(toolkit_tools) if toolkit_tools else 0
                logger.debug("Found %d tools for %s", tool_count, toolkit)

                if toolkit_tools:
                    for tool in toolkit_tools:
                        try:
                            if isinstance(tool, dict) and "function" in tool:
                                function_info = tool["function"]
                                slug = function_info.get("name")
                                description = function_info.get("description", "")
                                parameters = function_info.get("parameters", {})
                            else:
                                slug = tool.get("slug") or tool.get("name")
                                description = tool.get("description", "")
                                parameters = tool.get("parameters", {})

                            if not slug:
                                continue

                            wrapped_tool = ComposioToolWrapper(
                                composio_client=self.composio_client,
                                action_name=slug,
                                toolkit_name=toolkit,
                                description=description,
                                parameters=parameters,
                                user_id=self.user_id,
                            )
                            all_tools.append(wrapped_tool)
                        except Exception as e:
                            logger.error("Tool setup failed: %s", e)

            except Exception as e:
                logger.error("Toolkit setup failed for %s: %s", toolkit, e)

        return all_tools

    # ------------------------------------------------------------------
    # Public run interface
    # ------------------------------------------------------------------

    async def run(
        self,
        input_data: str,
        on_step: Optional[Callable[[str], None]] = None,
    ) -> RunResult:
        """
        Process user input and return a structured RunResult.

        This is an async coroutine. Use run_sync() for synchronous callers.
        """
        logger.info("Agent '%s' processing request", self.name)

        if not self.tools:
            logger.debug("Basic mode — no tools, responding directly")
            if on_step:
                on_step("Generating response...")
            current_prompt = self._build_basic_prompt(input_data)
            response = self._model_instance.get_response(current_prompt)
            return RunResult(output=response, stop_reason="stop")

        return await self._run_with_native_tools(input_data, on_step)

    def run_sync(
        self,
        input_data: str,
        on_step: Optional[Callable[[str], None]] = None,
    ) -> RunResult:
        """
        Synchronous wrapper around run().

        Suitable for scripts, notebooks, and frameworks that are not async-first.
        """
        return asyncio.run(self.run(input_data, on_step))

    # ------------------------------------------------------------------
    # Internal agentic loop
    # ------------------------------------------------------------------

    async def _run_with_native_tools(
        self,
        input_data: str,
        on_step: Optional[Callable[[str], None]],
    ) -> RunResult:
        """Agentic loop using the model's native function-calling API."""
        openai_tools = self._tools_to_openai_format()
        logger.debug(
            "Running with %d tools: %s",
            len(openai_tools),
            [t["function"]["name"] for t in openai_tools],
        )

        messages: List[Dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": input_data},
        ]
        all_tool_calls: List[Dict] = []

        for iteration in range(self.max_iterations):
            logger.debug("Iteration %d/%d", iteration + 1, self.max_iterations)

            result = await asyncio.to_thread(
                self._model_instance.get_response_with_tools, messages, openai_tools
            )

            if not result.get("tool_calls"):
                # Model gave a final text answer.
                logger.info("Agent '%s' produced final response", self.name)
                if on_step:
                    on_step("Generating response...")
                return RunResult(
                    output=result.get("text") or "",
                    stop_reason="stop",
                    tool_calls=all_tool_calls,
                    usage=result.get("usage"),
                )

            # Append the assistant's tool-call turn to the conversation.
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"]),
                        },
                    }
                    for tc in result["tool_calls"]
                ],
            })

            for tc in result["tool_calls"]:
                if on_step:
                    on_step(f"Using tool: {tc['name']}")
                try:
                    tool_result = self._execute_tool(tc["name"], tc["args"])
                    logger.debug("Tool %s → %s", tc["name"], str(tool_result)[:120])
                except Exception as e:
                    tool_result = f"Error executing tool: {e}"
                    logger.error("Tool %s failed: %s", tc["name"], e)

                all_tool_calls.append({
                    "name": tc["name"],
                    "args": tc["args"],
                    "result": tool_result,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result,
                })

        logger.warning(
            "Agent '%s' reached max_iterations (%d)", self.name, self.max_iterations
        )
        return RunResult(
            output="",
            stop_reason="max_iterations",
            tool_calls=all_tool_calls,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tools_to_openai_format(self) -> List[Dict]:
        """Convert tool list to OpenAI function-calling schema."""
        result = []
        for tool in self.tools:
            params = tool.get_parameters_schema() if hasattr(tool, "get_parameters_schema") else {}
            if not isinstance(params, dict):
                params = {}
            if "type" not in params:
                params = {"type": "object", "properties": params if params else {}}
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "parameters": params,
                },
            })
        return result

    def _execute_tool(self, tool_name: str, tool_input: Any) -> str:
        """Execute a tool by name with given input."""
        logger.debug("Executing tool: %s", tool_name)
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.run(tool_input)
        # Partial-match fallback
        for tool in self.tools:
            if tool_name.lower() in tool.name.lower() or tool.name.lower() in tool_name.lower():
                logger.debug("Partial match: using tool '%s' for '%s'", tool.name, tool_name)
                return tool.run(tool_input)
        available = [tool.name for tool in self.tools]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available}")

    def _build_basic_prompt(self, input_data: str) -> str:
        """Build basic prompt for agents without tools."""
        return (
            "You are an AI assistant that listens carefully to the user's input "
            "and provides a thoughtful response.\n\n"
            f"User input: {input_data}\n\n"
            "Please provide a helpful and informative response to the user's question or request."
        )

    # ------------------------------------------------------------------
    # Auth cache utilities
    # ------------------------------------------------------------------

    def clear_auth_cache(self):
        """Clear authentication cache for this agent."""
        if self.auth_cache:
            self.auth_cache.clear_cache()
            logger.info("Authentication cache cleared for agent '%s'", self.name)

    def get_auth_cache_status(self) -> Dict:
        """Get current authentication cache status."""
        if self.auth_cache:
            return self.auth_cache.get_cache_status()
        return {}
