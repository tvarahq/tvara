from tvara.core import Agent, Prompt
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

headlines_agent = Agent(
    name="Headlines Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a news Headlines generator. Generate a concise headline given the context to you."
    )
)

result_1 = basic_agent.run("get me the readme of a repo called speechLM by ashishlal2003 on GitHub")
result_2 = summarizer_agent.run(f"summarize the following content: {result_1}")
# result_3 = headlines_agent.run(f"generate a concise headline for the following summary: {result_2}")
result_4 = slack_agent.run(f"post the following summary to my Slack channel called all-tvara in a sad and depressed tone: {result_2}")

print(f"{blue}Everything done!{reset}")
