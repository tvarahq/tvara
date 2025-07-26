import datetime
from .BaseTool import BaseTool

class DateTool(BaseTool):
    def __init__(self):
        super().__init__(name="date_tool", description="Returns the current date.")

    def run(self, input_data: str) -> str:
        return f"Today's date is {datetime.date.today()}. Today's day is {datetime.date.today().strftime('%A')}. The current time is {datetime.datetime.now().strftime('%H:%M:%S')}."
