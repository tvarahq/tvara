import hashlib
import json
import threading
from typing import Awaitable, Callable, Dict, Optional

from tvara.core import Agent

# ---------------------------------------------------------------------------
# Process-level Agent cache
# ---------------------------------------------------------------------------
# Keyed by a fingerprint of (model, composio_api_key, sorted connected_accounts).
# Avoids re-fetching Composio tool schemas on every message for the same user.
# Thread-safe via a lock — the server runs the SDK in a thread executor.

_agent_cache: Dict[str, Agent] = {}
_agent_cache_lock = threading.Lock()


def _cache_key(
    model: str,
    composio_api_key: str,
    connected_accounts: Dict[str, str],
) -> str:
    """Stable cache key that changes whenever the user's connections change."""
    payload = {
        "model": model,
        "composio_api_key": composio_api_key,
        # Sort so dict ordering doesn't produce spurious misses.
        "accounts": sorted(connected_accounts.items()),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def run_for_user(
    connected_accounts: Dict[str, str],
    task: str,
    model: str,
    api_key: str,
    composio_api_key: str,
    on_step: Optional[Callable[[str], None]] = None,
    on_token: Optional[Callable[[str], Awaitable[None]]] = None,
    system_prompt: Optional[str] = None,
    max_iterations: int = 10,
) -> str:
    """
    Execute an agentic task on behalf of a user with pre-authenticated Composio connections.

    Args:
        connected_accounts: Dict mapping toolkit_slug -> connected_account_id for all
                            of the user's active connections, e.g.:
                            {"gmail": "ca_xxx", "github": "ca_yyy"}
                            The backend retrieves this from the user_connections DB table.
                            OAuth is skipped entirely — the connected_account_id is passed
                            directly to Composio for tool execution.
        task: Natural language task description (e.g. "send an email to xyz@gmail.com").
        model: LLM model name (e.g. "gemini-2.5-flash", "gpt-4o", "claude-sonnet-4-6").
        api_key: API key for the LLM provider.
        composio_api_key: Composio platform API key.
        on_step: Optional sync callback invoked on each agent step with a human-readable
                 description. Use this for streaming progress to the frontend.
        on_token: Optional async callback invoked for each streamed text token. When
                  provided, the model's streaming API is used instead of the blocking
                  call. Only text tokens are forwarded; tool-call arguments are not.
        max_iterations: Maximum agentic loop iterations (default 10).

    Returns:
        The agent's final response as a string.
    """
    key = _cache_key(model, composio_api_key, connected_accounts)

    with _agent_cache_lock:
        agent = _agent_cache.get(key)

    if agent is None:
        agent = Agent(
            name="tvara-agent",
            model=model,
            api_key=api_key,
            composio_api_key=composio_api_key,
            connected_accounts=connected_accounts,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
        )
        with _agent_cache_lock:
            _agent_cache[key] = agent
    else:
        # Update system_prompt in case it changed (e.g. user connected a new
        # integration between messages — the prompt is rebuilt server-side).
        agent.system_prompt = system_prompt or agent.system_prompt

    result = agent.run_sync(task, on_step=on_step, on_token=on_token)
    return result.output
