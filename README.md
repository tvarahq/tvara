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

---

## 🚀 Installation

Install Tvara using pip:

```bash
pip install tvara
```

## Basic Usage
Here's a simple example of how to define and run an agent:

```python
from tvara.core.agent import Agent

agent = Agent(
    name="TvaraScheduler",
    model="gemini-pro",
    api_key="your-api-key",
    prompt_template_name="basic_prompt_template",
    prompt_variables={
        "name": "TvaraScheduler",
        "description": "An assistant that helps schedule meetings intelligently."
    },
    tools=["calendar", "email_parser", "timezone_converter"],
    connectors=["google_calendar", "outlook_api"]
)

response = agent.run("Schedule a call with John next week.")
print(response)
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