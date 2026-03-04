from typing import Awaitable, Callable, Dict, Optional

from tvara.core import Agent


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
    agent = Agent(
        name="tvara-agent",
        model=model,
        api_key=api_key,
        composio_api_key=composio_api_key,
        connected_accounts=connected_accounts,
        system_prompt=system_prompt,
        max_iterations=max_iterations,
    )
    result = agent.run_sync(task, on_step=on_step, on_token=on_token)
    return result.output
