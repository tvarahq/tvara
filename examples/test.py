from tvara.core import Agent, Prompt
from tvara.connectors import NotionConnector
from tvara.tools import DateTool
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

my_prompt = Prompt(raw_prompt="You are a fucked up agent depressed in life.")

notion_agent = Agent(
    name="Notion Agent",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    connectors=[NotionConnector(token=NOTION_API_KEY)],
    tools=[DateTool()],
    prompt=my_prompt,
)

print(notion_agent.run("Yo bro, whats todays date? and timeeeee heheheheh"))