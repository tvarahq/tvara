# Tvara
<p align="center">
  <img src="https://raw.githubusercontent.com/tvarahq/tvara/main/assets/tvara_full_logo.png" alt="Tvara" />
</p>

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Website](https://img.shields.io/badge/Website-Tvara-green.svg)](https://tvarahq.com)
[![Slack](https://img.shields.io/badge/Slack-Join%20Us-purple.svg)](https://join.slack.com/t/tvara-workspace/shared_invite/zt-3b23aa3uu-dlcGm5pk~bg8_aF6loz3og)
[![PyPI](https://img.shields.io/badge/PyPI-Install%20Now-blue.svg)](https://pypi.org/project/tvara/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/tvarahq/tvara/blob/main/LICENSE)

**Tvara** is a powerful Python SDK for building intelligent, multi-agent AI workflows with minimal boilerplate. Unlike traditional frameworks, Tvara emphasizes plug-and-play simplicity with native Composio integration, offering access to 10,000+ tools and services through a unified interface.

Whether you're building personal automation, customer support systems, or complex agentic applications, Tvara lets you focus on what your agents do, not how to wire them together.

Whether you're building a personal automation, customer support bot, or a full-fledged agentic app, Tvara lets you focus on what your agents do, not how to wire them together.

---

## Key Features

- **Smart AI Agents** - Support for multiple LLM providers (Gemini, OpenAI, Anthropic)  
- **10,000+ Tools** - Native Composio integration with extensive toolkit ecosystem  
- **Multi-Agent Workflows** - Sequential and supervised agent coordination  
- **Smart Auth Caching** - Automatic authentication caching with configurable expiry  
- **Flexible Prompting** - Template-based and raw prompt support  
- **Rich Logging** - Comprehensive execution tracking with colored console output  
- **Robust Error Handling** - Intelligent retry mechanisms and graceful failure handling  
- **Easy Integration** - Minimal setup with powerful customization options  

**Coming Soon:** Visual workflow builder, advanced orchestration patterns, deployment tools, and enhanced observability dashboard.

---

## Quick Start

### Installation

```bash
pip install tvara
```

### Supported Models

- Gemini
- OpenAI
- Anthropic

### Basic Agent Usage

```python
from tvara.core import Agent
from dotenv import load_dotenv
import os

load_dotenv()

# Simple agent without tools
agent = Agent(
    name="MyAgent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
)

response = agent.run("Hi, how are you?")
print(response)
```

### Agent with Composio Tools

```python
from tvara.core import Agent
from dotenv import load_dotenv
import os

load_dotenv()

# Agent with Notion integration
notion_agent = Agent(
    name="My Notion Agent",
    model="gemini-2.5-flash", 
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["notion"],
)

response = notion_agent.run("Summarize my 'Project Ideas' page from Notion")
print(response)
```

### Advanced Agent Configuration

```python
from tvara.core import Agent, Prompt
from dotenv import load_dotenv
import os

load_dotenv()

# Custom prompt with multiple toolkits
custom_prompt = Prompt(
    raw_prompt="You are an anxious AI assistant who helps with tasks but worries about everything. Use tools when necessary."
)

multi_tool_agent = Agent(
    name="Multi-Tool Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["COMPOSIO_SEARCH", "slack"],
    prompt=custom_prompt,
    max_iterations=15,
    cache_auth=True,
    cache_validity_minutes=30
)

response = multi_tool_agent.run("Check the latest tech news headlines and send a summary to #dev-team on Slack")
print(response)
```

## Workflow Orchestration

### Sequential Workflow

Perfect for data processing pipelines where each agent builds on the previous output.

```python
from tvara.core import Agent, Workflow, Prompt
import os
from dotenv import load_dotenv

load_dotenv()

# Research agent with web search
researcher_agent = Agent(
    name="Researcher Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a researcher. Gather comprehensive information on the given topic and provide detailed insights."
    ),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["COMPOSIO_SEARCH"]
)

# Blog writer agent
blog_agent = Agent(
    name="Blog Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a professional blog writer. Create engaging, well-structured content from research data."
    )
)

# Create sequential workflow
research_workflow = Workflow(
    name="Research to Blog Pipeline",
    agents=[researcher_agent, blog_agent],
    mode="sequential",
    max_iterations=5,
)

result = research_workflow.run("Write a comprehensive blog post about the latest developments in quantum computing")
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

# Specialized worker agents
weather_agent = Agent(
    name="Weather Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["WEATHERMAP"],
)

poet_agent = Agent(
    name="Poet Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a creative poet who writes beautiful, evocative poetry about any topic."
    )
)

gmail_agent = Agent(
    name="Gmail Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["gmail"]
)

# Manager agent for coordination
manager_agent = Agent(
    name="Manager Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a workflow manager coordinating multiple AI agents. Analyze requests and delegate tasks efficiently."
    )
)

# Create supervised workflow
creative_workflow = Workflow(
    name="Weather Poetry Email",
    agents=[weather_agent, poet_agent, gmail_agent],
    mode="supervised",
    manager_agent=manager_agent,
    max_iterations=10
)

result = creative_workflow.run("Get San Francisco weather, write a poem about it, and email it to team@tvarahq.com")
print(f"Workflow Result: {result.final_output}")
print(f"Agent Outputs: {len(result.agent_outputs)} steps completed")
```

## Configuration & Customization

### Environment Variables

Create a `.env` file in your project root:

```plaintext
# Required: LLM API Keys
MODEL_API_KEY=your_gemini_or_openai__or_claude_key

# Required for tools: Composio API Key
COMPOSIO_API_KEY=your_composio_api_key
```

### Authentication Caching

Tvara includes smart authentication caching to avoid repeated OAuth flows:

```python
# Enable caching (default)
agent = Agent(
    name="Cached Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["github", "slack"],
    cache_auth=True,  # Enable caching
    cache_validity_minutes=30,  # Cache for 30 minutes
)

# Check cache status
cache_status = agent.get_auth_cache_status()
print(cache_status)

# Clear cache manually
agent.clear_auth_cache()
```

The cache will automatically expire after the specified validity period (defaulting to 10 minutes), ensuring that stale tokens are not used. The cache is stored by default in `./cache/` directory.

### Custom Prompts

```python
from tvara.core import Prompt
from tvara.utils.prompt_templates import template_registry

# Using built-in templates
basic_prompt = Prompt(template_name="basic_prompt_template")
agent_prompt = Prompt(template_name="agent_prompt_template")

# Custom raw prompts
custom_prompt = Prompt(
    raw_prompt="""You are a helpful AI assistant specialized in data analysis.
    You should be thorough, accurate, and provide actionable insights.
    Always cite sources when using external data."""
)

# View available templates
print("Available templates:", list(template_registry.keys()))
```

## Available Toolkits

Tvara provides access to 10,000+ tools through Composio integration.


### Complete Composio Toolkits Reference

### No Authentication Required

```python
# These toolkits work immediately without OAuth
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
    # Popular authenticated toolkits
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
        "instagram",         # Photo and content sharing
    ]
    project_management_toolkits = [
        "trello",            # Board-based project management
        "asana",             # Task and project tracking
        "jira",              # Issue tracking and agile
        "monday",            # Work management platform
        "clickup",           # All-in-one workspace
    ]
    communication_toolkits = [
        "zoom",              # Video conferencing
        "discord",           # Community and gaming chat
        "teams",             # Microsoft Teams integration
        "whatsapp",         # Messaging platform
    ]
    development_toolkits = [
        "gitlab",            # Git repository hosting
        "bitbucket",         # Atlassian git solution
        "docker",            # Containerization platform
        "aws",               # Amazon Web Services
        "gcp",               # Google Cloud Platform
        "azure",             # Microsoft Azure
    ]
```

### Finding All Available Toolkits

```python
# Programmatically discover available toolkits
from composio import Composio
client = Composio(api_key="your_composio_api_key")
available_toolkits = client.toolkits.list()
for toolkit in available_toolkits:
    print(f"Toolkit: {toolkit.name}")
    print(f"Description: {toolkit.description}")
    print(f"Auth Required: {toolkit.requires_auth}")
    print("---")
```

### Usage Example

```python
# Multiple toolkits in one agent
productivity_agent = Agent(
    name="Productivity Assistant",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=[
        "github",           # Code management
        "slack",            # Team communication  
        "google_calendar",  # Scheduling
        "notion",           # Documentation
        "gmail"             # Email
    ],
)
```

## Workflow Management

### WorkflowResult Object

Every workflow execution returns a comprehensive result object:

```python
result = workflow.run("Your request here")

# Access results
print(f"Success: {result.success}")
print(f"Final Output: {result.final_output}")
print(f"Error (if any): {result.error}")

# Detailed agent outputs
for output in result.agent_outputs:
    print(f"Agent: {output['agent_name']}")
    print(f"Input: {output['input']}")
    print(f"Output: {output['output']}")
    print(f"Step: {output.get('step', 'N/A')}")
```

### Workflow Management Methods

```python
# Create workflow
workflow = Workflow(
    name="My Workflow",
    agents=[agent1, agent2],
    mode="sequential"
)

# Add/remove agents dynamically
workflow.add_agent(new_agent)
workflow.remove_agent("Agent Name")

# Get workflow summary
summary = workflow.get_workflow_summary()
print(summary)

# Output:
# {
#     "name": "My Workflow",
#     "mode": "sequential", 
#     "agent_count": 2,
#     "agent_names": ["Agent1", "Agent2"],
#     "has_manager": False,
#     "max_iterations": 10
# }
```

## Best Practices

1. **Agent Design**
- Use descriptive names for agents and workflows
- Provide clear, specific prompts for better performance
- Limit toolkits to what's actually needed
- Set appropriate max_iterations based on task complexity

2. **Error Handling**
```python
try:
    result = workflow.run("Complex task")
    if result.success:
        print(f"Success: {result.final_output}")
    else:
        print(f"Workflow failed: {result.error}")
except Exception as e:
    print(f"Execution error: {e}")
```

3. Authentication Management

- Use environment variables for API keys
- Enable caching for frequently used toolkits
- Set reasonable cache expiry times
- Clear cache when switching between different accounts

4. Workflow Design

- Sequential: Use for linear data processing pipelines
- Supervised: Use for complex tasks requiring dynamic decisions
- Keep workflows focused on specific use cases
- Monitor agent outputs for debugging

## Debugging & Monitoring

Tvara provides rich console logging with color-coded output:

- 🤖 Blue: Agent initialization and basic info
- ✅ Green: Successful operations
- ⚠️ Yellow: Warnings and fallbacks
- ❌ Red: Errors and failures
- 🔧 Cyan: Tool and workflow operations
- 👨‍💼 Purple: Manager decisions and workflow orchestration

### Logging Control

```python
# Enable/disable detailed logging
workflow = Workflow(
    name="Debug Workflow",
    agents=[agent],
    enable_logging=True  # Set to False for quiet mode
)
```

## Requirements

- Python: 3.9 or higher

- Required Dependencies:
  - google-genai ^1.27.0
  - openai 1.99.9
  - anthropic ^0.61.0
  - composio 0.8.0
  - pydantic 2.11.7
  - tavily-python ^0.7.10

## Contributing

We welcome contributions to Tvara!

- Report Issues: Found a bug? Open an issue with detailed reproduction steps
- Feature Requests: Share your ideas
- Code Contributions: Submit PRs for bug fixes or new features
- Documentation: Help improve guides and examples
- Community: Share your Tvara projects and use cases
- Check our Contributing Guide for detailed guidelines.

## License

Tvara is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## What's Next?

- Visual Workflow Builder - Drag-and-drop interface for complex workflows
- Advanced Orchestration - Parallel and conditional execution modes
- Deployment Tools - One-click deployment to cloud platforms
- Enhanced Observability - Real-time monitoring and analytics dashboard
- Custom Tool Development - SDK for building your own tool integrations

---

Built with ❤️ by the Tvara Community

Ready to build something amazing? Start with our [examples](examples) directory or join our [Slack](https://join.slack.com/t/tvara-workspace/shared_invite/zt-3b23aa3uu-dlcGm5pk~bg8_aF6loz3og) community for support and discussions.