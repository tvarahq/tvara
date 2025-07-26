from .base import BaseTool

class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(name="calculator_tool", description="Performs basic calculations.")

    def run(self, input_data: str) -> str:
        try:
            result = eval(input_data)
            return f"The result of the calculation is: {result}"
        except Exception as e:
            return f"Error occurred: {str(e)}"
