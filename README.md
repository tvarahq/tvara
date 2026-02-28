# Tvara
<p align="center">
  <img src="https://raw.githubusercontent.com/tvarahq/tvara/refs/heads/main/docs/images/updated_logo.png" alt="Tvara" />
</p>

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Website](https://img.shields.io/badge/Website-Tvara-green.svg)](https://tvarahq.com)
[![Slack](https://img.shields.io/badge/Slack-Join%20Us-purple.svg)](https://join.slack.com/t/tvara-workspace/shared_invite/zt-3b23aa3uu-dlcGm5pk~bg8_aF6loz3og)
[![PyPI](https://img.shields.io/badge/PyPI-Install%20Now-blue.svg)](https://pypi.org/project/tvara/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/tvarahq/tvara/blob/main/LICENSE)

**Tvara** is a powerful Python SDK for building intelligent, multi-agent AI workflows with minimal boilerplate. Unlike traditional frameworks, Tvara emphasizes plug-and-play simplicity with native Composio integration, offering access to 10,000+ tools and services through a unified interface.

Whether you're building personal automation, customer support systems, or complex agentic applications, Tvara lets you focus on what your agents do, not how to wire them together.

---

## Key Features

- **Smart AI Agents** — Support for multiple LLM providers (Gemini, OpenAI, Anthropic) with native function calling for all models
- **10,000+ Tools** — Native Composio integration with an extensive toolkit ecosystem
- **Multi-Agent Workflows** — Sequential and supervised agent coordination
- **Structured Results** — `RunResult` dataclass with output, stop reason, tool call history, and token usage
- **Async-First** — `await agent.run()` works natively in async frameworks (FastAPI, etc.); `run_sync()` for scripts
- **Smart Auth Caching** — Automatic authentication caching with configurable expiry
- **Flexible Prompting** — Template-based and raw prompt support
- **Library-Grade Logging** — Uses Python's standard `logging` module; callers control output verbosity
- **Easy Integration** — Minimal setup with powerful customization options

**Coming Soon:** Visual workflow builder, advanced orchestration patterns, deployment tools, and enhanced observability dashboard.

---

## Quick Start

### Installation

```bash
pip install tvara
```

### Supported Models

| Provider | Example model strings |
|---|---|
| Google Gemini | `gemini-2.0-flash`, `gemini-2.5-flash` |
| OpenAI | `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `claude-sonnet-4-6`, `claude-opus-4-6` |

### Basic Agent Usage

```python
from tvara.core import Agent
from dotenv import load_dotenv
import os

load_dotenv()

agent = Agent(
    name="MyAgent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
)

result = agent.run_sync("Hi, how are you?")
print(result.output)
```

### Agent with Composio Tools

```python
from tvara.core import Agent
from dotenv import load_dotenv
import os

load_dotenv()

notion_agent = Agent(
    name="My Notion Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["notion"],
)

result = notion_agent.run_sync("Summarize my 'Project Ideas' page from Notion")
print(result.output)
```

### Async Usage (FastAPI, etc.)

```python
from tvara.core import Agent
import os

agent = Agent(
    name="AsyncAgent",
    model="gpt-4o",
    api_key=os.getenv("MODEL_API_KEY"),
)

# await directly — no event-loop blocking
result = await agent.run("Summarize the latest news.")
print(result.output)
```

---

## RunResult

Every `agent.run()` / `agent.run_sync()` call returns a `RunResult`:

```python
from tvara import RunResult  # or: from tvara.core import RunResult

result = agent.run_sync("Send an email to alice@example.com")

print(result.output)        # str — the agent's final answer
print(result.stop_reason)   # "stop" | "max_iterations" | "error"
print(result.tool_calls)    # list of {name, args, result} dicts — one entry per tool invoked
print(result.usage)         # dict with input_tokens / output_tokens (if the model reports them)
```

| Field | Type | Description |
|---|---|---|
| `output` | `str` | The agent's final response text |
| `stop_reason` | `Literal["stop", "max_iterations", "error"]` | Why the loop ended |
| `tool_calls` | `list[dict]` | Ordered record of every tool call made |
| `usage` | `dict \| None` | Token counts (`input_tokens`, `output_tokens`) |

```python
# Distinguish a real answer from a loop timeout
if result.stop_reason == "max_iterations":
    print("Agent hit the iteration limit — try increasing max_iterations or simplifying the task.")
else:
    print(result.output)
```

---

## Backend / Server Usage

For server-side applications where users' Composio connections are already established, use `run_for_user` to skip OAuth entirely:

```python
from tvara import run_for_user

# connected_accounts maps toolkit_slug → connected_account_id
# retrieved from your user_connections database table
output: str = run_for_user(
    connected_accounts={"gmail": "ca_xxx", "github": "ca_yyy"},
    task="Open a GitHub issue for the bug described in my latest email",
    model="gpt-4o",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    on_step=lambda step: print(f"[step] {step}"),  # optional progress callback
    max_iterations=10,
)
print(output)
```

`run_for_user` returns the agent's final response as a plain `str` for backwards compatibility with existing callers.

---

## Advanced Agent Configuration

```python
from tvara.core import Agent, Prompt
from dotenv import load_dotenv
import os

load_dotenv()

custom_prompt = Prompt(
    raw_prompt="You are an AI assistant who helps with tasks and always uses tools when available."
)

multi_tool_agent = Agent(
    name="Multi-Tool Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["COMPOSIO_SEARCH", "slack"],
    prompt=custom_prompt,
    max_iterations=15,
    cache_auth=True,
    cache_validity_minutes=30,
)

result = multi_tool_agent.run_sync(
    "Check the latest tech news headlines and send a summary to #dev-team on Slack"
)
print(result.output)
```

---

## Workflow Orchestration

### Sequential Workflow

Perfect for data processing pipelines where each agent builds on the previous output.

```python
from tvara.core import Agent, Workflow, Prompt
import os
from dotenv import load_dotenv

load_dotenv()

researcher_agent = Agent(
    name="Researcher Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a researcher. Gather comprehensive information on the given topic."
    ),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["COMPOSIO_SEARCH"],
)

blog_agent = Agent(
    name="Blog Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a professional blog writer. Create engaging content from research data."
    ),
)

research_workflow = Workflow(
    name="Research to Blog Pipeline",
    agents=[researcher_agent, blog_agent],
    mode="sequential",
    max_iterations=5,
)

result = research_workflow.run("Write a blog post about the latest developments in quantum computing")
print(f"Final Output: {result.final_output}")
print(f"Success: {result.success}")
```

### Supervised Workflow

Ideal for complex tasks requiring dynamic decision-making and agent coordination.

```python
from tvara.core import Agent, Workflow, Prompt
from dotenv import load_dotenv
import os

load_dotenv()

weather_agent = Agent(
    name="Weather Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["WEATHERMAP"],
)

poet_agent = Agent(
    name="Poet Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(raw_prompt="You are a creative poet who writes beautiful poetry about any topic."),
)

gmail_agent = Agent(
    name="Gmail Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["gmail"],
)

manager_agent = Agent(
    name="Manager Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a workflow manager coordinating multiple AI agents. Delegate tasks efficiently."
    ),
)

creative_workflow = Workflow(
    name="Weather Poetry Email",
    agents=[weather_agent, poet_agent, gmail_agent],
    mode="supervised",
    manager_agent=manager_agent,
    max_iterations=10,
)

result = creative_workflow.run("Get San Francisco weather, write a poem about it, and email it to team@tvarahq.com")
print(f"Workflow Result: {result.final_output}")
print(f"Agent Outputs: {len(result.agent_outputs)} steps completed")
```

---

## Configuration & Customization

### Environment Variables

Create a `.env` file in your project root (see `.env.sample`):

```plaintext
MODEL_API_KEY=your_gemini_or_openai_or_claude_key
COMPOSIO_API_KEY=your_composio_api_key
```

### Get Composio API Key

To use tools and connectors with the SDK, you'll need a Composio API key.

1. Go to the [Composio Developer Portal](https://composio.dev).
2. Sign up or log in with your account.
3. Navigate to **Dashboard → API Keys**.
4. Click **Generate New Key**.
5. Paste it into your `.env` file as `COMPOSIO_API_KEY=your_composio_api_key`.

### Authentication Caching

Tvara includes smart authentication caching to avoid repeated OAuth flows:

```python
agent = Agent(
    name="Cached Agent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["github", "slack"],
    cache_auth=True,              # enabled by default
    cache_validity_minutes=30,
)

# Check cache status
print(agent.get_auth_cache_status())

# Clear manually
agent.clear_auth_cache()
```

The cache expires automatically after the configured validity period (default: 10 minutes) and is stored in `./cache/`.

### Custom Prompts

```python
from tvara.core import Prompt
from tvara.utils.prompt_templates import template_registry

# Built-in template
agent_prompt = Prompt(template_name="agent_prompt_template")

# Raw prompt
custom_prompt = Prompt(
    raw_prompt="""You are a helpful AI assistant specialised in data analysis.
    Be thorough, accurate, and provide actionable insights."""
)

# Discover available templates
print("Available templates:", list(template_registry.keys()))
```

---

## Available Toolkits

Tvara provides access to 10,000+ tools through Composio integration.

### No Authentication Required

```python
composio_toolkits = [
    "COMPOSIO_SEARCH",    # Web search and information retrieval
    "CODEINTERPRETER",    # Python code execution environment
    "WEATHERMAP",         # Weather data and forecasts
    "HACKERNEWS",         # Hacker News content and discussions
    "TEXT_TO_PDF",        # Document format conversion
    "ENTELLIGENCE",       # Intelligence and analytics tools
]
```

### Authentication Required

```python
productivity_toolkits = [
    "github",             # Repository management, issues, PRs
    "slack",              # Team communication and channels
    "gmail",              # Email management and automation
    "notion",             # Knowledge base and documents
    "google_calendar",    # Calendar and scheduling
    "google_drive",       # File storage and sharing
    "google_docs",        # Document creation and editing
    "google_sheets",      # Spreadsheet management
]
social_media_toolkits = [
    "twitter",            # Social media management
    "linkedin",           # Professional networking
    "facebook",           # Social platform integration
    "instagram",          # Photo and content sharing
]
project_management_toolkits = [
    "trello",             # Board-based project management
    "asana",              # Task and project tracking
    "jira",               # Issue tracking and agile
    "monday",             # Work management platform
    "clickup",            # All-in-one workspace
]
development_toolkits = [
    "gitlab",             # Git repository hosting
    "bitbucket",          # Atlassian git solution
    "aws",                # Amazon Web Services
    "gcp",                # Google Cloud Platform
    "azure",              # Microsoft Azure
]
```

### Finding All Available Toolkits

```python
from composio import Composio

client = Composio(api_key="your_composio_api_key")
for toolkit in client.toolkits.list():
    print(toolkit.name, "-", toolkit.description)
```

---

## Workflow Management

### WorkflowResult Object

Every workflow execution returns a comprehensive result object:

```python
result = workflow.run("Your request here")

print(f"Success: {result.success}")
print(f"Final Output: {result.final_output}")
print(f"Error (if any): {result.error}")

for output in result.agent_outputs:
    print(f"Agent: {output['agent_name']}")
    print(f"Input: {output['input']}")
    print(f"Output: {output['output']}")
```

### Workflow Management Methods

```python
workflow = Workflow(name="My Workflow", agents=[agent1, agent2], mode="sequential")

workflow.add_agent(new_agent)
workflow.remove_agent("Agent Name")

print(workflow.get_workflow_summary())
# {
#     "name": "My Workflow",
#     "mode": "sequential",
#     "agent_count": 2,
#     "agent_names": ["Agent1", "Agent2"],
#     "has_manager": False,
#     "max_iterations": 10
# }
```

---

## Best Practices

### Agent Design

- Use descriptive names for agents and workflows.
- Provide clear, specific prompts for better performance.
- Limit toolkits to what's actually needed.
- Set `max_iterations` based on task complexity (default: 10).

### Error Handling

```python
result = agent.run_sync("Complex task")

if result.stop_reason == "max_iterations":
    # Agent ran out of iterations — consider increasing max_iterations
    # or check result.tool_calls to see where it got stuck
    print(f"Timed out after {len(result.tool_calls)} tool calls")
elif result.stop_reason == "error":
    print("Agent encountered an error")
else:
    print(result.output)
```

For workflows:

```python
result = workflow.run("Complex workflow task")
if result.success:
    print(result.final_output)
else:
    print(f"Workflow failed: {result.error}")
```

### Authentication Management

- Use environment variables for API keys — never hard-code them.
- Enable caching (`cache_auth=True`) for frequently used toolkits.
- Set reasonable cache expiry times (`cache_validity_minutes`).
- Clear cache when switching between user accounts.

### Workflow Design

- **Sequential** — for linear data processing pipelines where step N feeds step N+1.
- **Supervised** — for complex tasks requiring dynamic routing between specialist agents.
- Keep workflows focused on a single use case for easier debugging.

---

## Logging

Tvara uses Python's standard `logging` module with a `NullHandler` — no output is emitted by default, keeping it safe for library use.

### Quick way: `verbose=True`

Pass `verbose=True` when constructing an `Agent` to turn on debug output for that agent without touching your application's logging config:

```python
agent = Agent(
    name="MyAgent",
    model="gemini-2.0-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    verbose=True,  # prints DEBUG logs to stdout
)
```

### Application-level control

If you want finer control (e.g. route logs to a file, change the level), configure the `tvara` logger directly:

```python
import logging

# Info-level only
logging.getLogger("tvara").setLevel(logging.INFO)
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")

# Full debug output
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
```

---

## Requirements

- Python 3.10 or higher

- Required Dependencies:
  - `google-genai ^1.27.0`
  - `openai 1.99.9`
  - `anthropic ^0.61.0`
  - `composio 0.8.0`
  - `pydantic 2.11.7`

---

## Contributing

We welcome contributions to Tvara!

- **Report Issues** — Found a bug? Open an issue with detailed reproduction steps.
- **Feature Requests** — Share your ideas.
- **Code Contributions** — Submit PRs for bug fixes or new features.
- **Documentation** — Help improve guides and examples.
- **Community** — Share your Tvara projects and use cases.

Check our Contributing Guide for detailed guidelines.

---

## License

Tvara is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

---

## What's Next?

- Visual Workflow Builder — Drag-and-drop interface for complex workflows
- Advanced Orchestration — Parallel and conditional execution modes
- Deployment Tools — One-click deployment to cloud platforms
- Enhanced Observability — Real-time monitoring and analytics dashboard
- Custom Tool Development — SDK for building your own tool integrations

---

Built with ❤️ by the Tvara Community

Ready to build something amazing? Start with our [examples](examples) directory or join our [Slack](https://join.slack.com/t/tvara-workspace/shared_invite/zt-3b23aa3uu-dlcGm5pk~bg8_aF6loz3og) community for support and discussions.
