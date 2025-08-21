class CustomToolWrapper:
    def __init__(self, name: str, func: callable, description: str = "", parameters: dict = None):
        self.name = name
        self.func = func
        self.description = description
        self.parameters = parameters or {}

    def run(self, tool_input: dict):
        try:
            return self.func(**tool_input) if isinstance(tool_input, dict) else self.func(tool_input)
        except Exception as e:
            return f"Error in custom tool '{self.name}': {str(e)}"
