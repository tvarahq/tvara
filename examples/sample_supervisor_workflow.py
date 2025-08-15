from tvara.core import Agent, Workflow, Prompt
from dotenv import load_dotenv
import os

load_dotenv()

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
)

gmail_agent = Agent(
    name="Gmail Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    composio_api_key=os.getenv("COMPOSIO_API_KEY"),
    composio_toolkits=["gmail"]
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
    agents=[weather_agent, poet_agent, gmail_agent],
    mode= "supervised",
    manager_agent=manager_agent,
)

response = my_workflow.run("get the latest weather of sanfrancisco, write about it in a poetic way and send it to team@tvarahq.com on Gmail").final_output