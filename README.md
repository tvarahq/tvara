# Tvara
![Tvara](assets/Tvara_Stretched.png)

**Tvara** is a powerful Python SDK for building intelligent AI agents with tools, connectors, and multi-agent workflows. Create sophisticated AI systems that can interact with external services, execute code, search the web, and coordinate multiple agents seamlessly.

---

## ✨ Features

- 🤖 **Smart AI Agents** - Create agents with different models (Gemini, OpenAI, etc.)
- 🛠️ **Built-in Tools** - Web search, code execution, calculations, date/time utilities
- 🔗 **External Connectors** - GitHub, Slack integrations with more coming
- 🔄 **Multi-Agent Workflows** - Sequential and supervised agent coordination
- 📝 **Flexible Prompting** - Template-based and raw prompt support
- 🎯 **Easy Integration** - Simple API with comprehensive error handling
- 🔧 **Extensible Architecture** - Easy to add custom tools and connectors

> * Coming soon: Better workflow orchestration, multi-step agent execution, role-based behavior, and a visual interface for building agents and workflows.

---

## Roadmap
- Connectors for SQL databases, cloud storage, APIs, and more
- Workflow orchestration with multi-step agent execution
- Multi-agent coordination and role-based behavior
- Visual interface for building and deploying agents
- Improved observability and logs for debugging

Stay tuned for the official V1 launch, where these features will be included as part of our stable release.

## 🚀 Quick Start

### Installation

```bash
pip install tvara
```

## Usage Guide
You can refer to the [examples](examples/) directory for more detailed usage patterns. Below is a simple example of creating and running an agent:

```python
from tvara.core import Agent

agent = Agent(
    name="MyAgent",
    model="gemini-pro",
    api_key="your-api-key",
)

response = agent.run("Hi, how are you?")
print(response)
```

To create a more complex agent with specific tools and custom system prompts, you can do the following:

```python
from tvara.core.agent import Agent
from tvara.core.prompt import Prompt
from tvara.tools import WebSearchTool, DateTool, CodeTool

my_anxious_prompt = Prompt(
    raw_prompt="You are a very anxious AI assistant. You will answer the user's questions but in a very anxious manner. You will also use the tools provided to you.",
    tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool(), CodeTool()],
)

agent = Agent(
    name="TvaraCoder",
    model="gemini-pro",
    api_key="your-api-key",
    prompt=my_anxious_prompt,
    prompt_variables={
        "name": "TvaraCoder",
        "description": "An assistant that helps with coding tasks."
    },
    tools=["code_executor", "debugger", "api_client"],
)

response = agent.run("List out all files in my current working directory using Python.")
print(response)
```

An example of a sequential workflow with multiple agents:

```python
from tvara.core import Agent, Workflow, Prompt
from tvara.tools import DateTool, WebSearchTool
import os
from dotenv import load_dotenv

load_dotenv()

researcher_agent = Agent(
    name="Researcher Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a researcher tasked with gathering information on a specific topic. Use the tools available to you to find relevant information and summarize it.",
        tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool()]
    )
)

blog_agent = Agent(
    name="Blog Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a blog writer. Use the information provided by the Researcher Agent to write a comprehensive blog post.",
    )
)

my_workflow = Workflow(
    name="Sample Sequential Workflow",
    agents=[researcher_agent, blog_agent],
    mode="sequential",
    max_iterations=3,
)

result = my_workflow.run("Write a blog post under the name of Tvara Community about the latest advancements in AI research.")

print(f"Workflow Result: {result.final_output}")
print(f"Workflow summary: {my_workflow.get_workflow_summary()}")
```

An example of a supervised workflow with multiple agents:

```python
from tvara.core import Agent, Workflow, Prompt
from tvara.tools import DateTool, WebSearchTool, CodeTool
from tvara.connectors import GitHubConnector, SlackConnector
from dotenv import load_dotenv
import os

load_dotenv()

basic_agent = Agent(
    name="GitHub Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool(), CodeTool()],
    connectors=[GitHubConnector(name="github", token=os.getenv("GITHUB_PAT"))]
)

summarizer_agent = Agent(
    name="Summarizer",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
)

slack_agent = Agent(
    name="Slack Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    connectors=[SlackConnector(name="slack", token=os.getenv("SLACK_BOT_TOKEN"))]
)

manager_agent = Agent(
    name="Manager Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a workflow manager coordinating multiple AI agents. Your job is to decide what should happen next."
    )
)

my_workflow = Workflow(
    name= "Sample Workflow",
    agents=[basic_agent, summarizer_agent, slack_agent],
    mode= "supervised",
    manager_agent=manager_agent,
    max_iterations=3,
)

result = my_workflow.run("Send the latest readme file of the tvara repository by tvarahq on GitHub to the Slack channel #test-conn. Ensure you send a summary only which is in a cheerful product launch business tone!")

print(f"Workflow Result: {result.final_output}")
print(f"Workflow summary: {my_workflow.get_workflow_summary()}")
```

### 🛠️ Available Tools

| Tool             | Description                      | Usage                   | Required Setup     |
|------------------|----------------------------------|--------------------------|---------------------|
| `WebSearchTool`  | Search the web using Tavily API | Research, fact-checking | `TAVILY_API_KEY`    |
| `CodeTool`       | Execute Python code snippets     | Code execution          | None                |
| `CalculatorTool` | Perform mathematical calculations| Basic math operations   | None                |
| `DateTool`       | Get current date and time        | Time-based queries      | None                |

---

### 🔗 Available Connectors

| Connector         | Description                    | Actions                              | Required Setup      |
|-------------------|--------------------------------|--------------------------------------|----------------------|
| `GitHubConnector` | Interact with GitHub repos     | List repos, manage issues, contents | `GITHUB_PAT`         |
| `SlackConnector`  | Interact with Slack workspace  | Send messages, upload files         | `SLACK_BOT_TOKEN`    |

To create your own tools, you can subclass `BaseTool` and implement the `run` method. For example:

```python
from tvara.tools.base import BaseTool
import requests
import json

class WeatherTool(BaseTool):
    def __init__(self, api_key: str):
        super().__init__(
            name="weather_tool", 
            description="Gets current weather information for any city"
        )
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def run(self, input_data: str) -> str:
        try:
            params = {
                'q': input_data.strip(),
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return f"""Weather in {data['name']}, {data['sys']['country']}:
Temperature: {data['main']['temp']}°C
Condition: {data['weather'][0]['description'].title()}
Humidity: {data['main']['humidity']}%
Wind Speed: {data['wind']['speed']} m/s"""
        except Exception as e:
            return f"Error: {str(e)}"
```

To create your own connectors, you can subclass `BaseConnector` and implement the necessary methods. For example:

```python
from tvara.connectors.base import BaseConnector
import requests
from typing import Dict, Any, Union

class DiscordConnector(BaseConnector):
    def __init__(self, name: str, bot_token: str):
        super().__init__(name)
        self.bot_token = bot_token
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        }
    
    def get_action_schema(self) -> dict:
        return {
            "send_message": {
                "description": "Send a message to a Discord channel",
                "parameters": {
                    "channel_id": {"type": "string", "required": True},
                    "content": {"type": "string", "required": True}
                }
            },
            "get_guild_info": {
                "description": "Get information about a Discord server/guild",
                "parameters": {
                    "guild_id": {"type": "string", "required": True}
                }
            },
            "list_channels": {
                "description": "List all channels in a Discord server",
                "parameters": {
                    "guild_id": {"type": "string", "required": True}
                }
            }
        }

    def run(self, action: str, input: dict) -> Union[Dict[Any, Any], str]:
        # Implementation similar to earlier
        pass
```

You may view the existing tools and connectors in the `tvara/tools` and `tvara/connectors` directories respectively.

For detailed documentation on how to create custom agents, tools, and prompts, we will be adding a comprehensive guide soon on our website.

## Environment Variables
To run Tvara, you may need to set up your environment variables for certain models, tools and connectors. Create a `.env` file in the root directory of your project with the following content:

```plaintext
MODEL_API_KEY
TAVILY_API_KEY
GITHUB_PAT
SLACK_BOT_TOKEN
```

## Prompt Templates
Tvara supports pre-defined prompt templates using a template registry:

```python
from tvara.utils.prompt_templates import template_registry

print(template_registry.keys())  # e.g., ['basic_prompt_template', 'tool_aware_template']
```

To write your own custom prompt, you can make use of the special `prompt_template` called `custom_prompt_template`:

```python
template_registry['custom_prompt_template']
```

## Requirements
- Python 3.8+
- API keys for chosen AI model (Gemini, OpenAI, etc.)
- Optional: Tavily API key for web search
- Optional: GitHub Personal Access Token
- Optional: Slack Bot Token

## Contributing
We welcome contributions to Tvara! Feel free to open issues, suggest features, or submit pull requests. Check the [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon) for more details.

## License
Tvara is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

Built with ❤️ by the Tvara Community