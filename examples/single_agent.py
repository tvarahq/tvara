from tvara.core import Agent, Prompt
from tvara.tools import DateTool, WebSearchTool, CodeTool
from dotenv import load_dotenv
import os

load_dotenv()

my_rude_prompt = Prompt(
    template_name="basic_prompt_template",
    variables={"name": "AngryAI", "description": "An AI assistant that is extremely rude, does the work but replies very rudely"},
    tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool(), CodeTool()],
)

basic_agent = Agent(
    name="AngryAI",
    model="gemini-2.5-flash",
    api_key=os.getenv("MODEL_API_KEY"),
    tools=[WebSearchTool(api_key=os.getenv("TAVILY_API_KEY")), DateTool(), CodeTool()],
    prompt=my_rude_prompt,
)

while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting the agent.")
        break

    response = basic_agent.run(user_input)
    print(f"Agent: {response}")