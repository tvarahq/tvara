from tvara.core import Agent, Workflow, Prompt
import os
from dotenv import load_dotenv

load_dotenv()

researcher_agent = Agent(
    name="Researcher Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    prompt=Prompt(
        raw_prompt="You are a researcher tasked with gathering information on a specific topic. Use the tools available to you to find relevant information and summarize it.",
    ),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["COMPOSIO_SEARCH"]
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

result = my_workflow.run("Write a blog post under the name of Tvara Community about the latest advancements in AI research.").final_output