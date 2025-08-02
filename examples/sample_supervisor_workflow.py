from tvara.core import Agent, Workflow, Prompt
from tvara.tools import DateTool, WebSearchTool, CodeTool
from tvara.connectors import GitHubConnector, SlackConnector
from dotenv import load_dotenv
import os

load_dotenv()

blue = "\033[94m"
reset = "\033[0m"

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

print(f"{blue}Workflow Result:{reset} {result.final_output}")
print(f"{blue}Workflow summary:{reset} {my_workflow.get_workflow_summary()}")