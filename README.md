# Tvara
![Tvara](assets/Tvara_Stretched.png)

**Tvara** is an open-source platform for developing and deploying intelligent AI agents. It offers a modular, extensible architecture for integrating models, tools, and data connectors into a single agent-driven interface.

## ✨ Features
- **Agent Framework**: Create, customize, and run intelligent agents using powerful language models.
- **Prompt Engineering**: Use templated prompts with dynamic variables, tools, and connectors.
- **Model Flexibility**: Support for pluggable models via a centralized model factory.
- **Extensible Design**: Easily plug in new models, tools, or connectors.
- **API Key Management**: Securely pass and manage credentials per agent.
- **Open Source**: Transparent and extensible by design.

> **Coming Soon:** Workflow orchestration, multi-agent coordination, and a visual interface.

## Roadmap
- Connectors for SQL databases, cloud storage, APIs, and more
- Workflow orchestration with multi-step agent execution
- Multi-agent coordination and role-based behavior
- Visual interface for building and deploying agents
- Improved observability and logs for debugging

Stay tuned for the official V1 launch, where these features will be included as part of our stable release.

## Installation

Install Tvara using pip:

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

To create your own tools, you can subclass `BaseTool` and implement the `run` method. For example:

```python
from tvara.tools import BaseTool
class MyCustomTool(BaseTool):
    def run(self, input_data):
        # Implement your tool logic here
        return f"Processed input: {input_data}"
```

For detailed documentation on how to create custom agents, tools, and prompts, we will be adding a comprehensive guide soon on our website.

## Environment Variables
To run Tvara, you may need to set up your environment variables for certain models and tools. Create a `.env` file in the root directory of your project with the following content:

```plaintext
MODEL_API_KEY
TAVILY_API_KEY
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

## Contributing
We welcome contributions to Tvara! Feel free to open issues, suggest features, or submit pull requests. Check the [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon) for more details.

## License
Tvara is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.