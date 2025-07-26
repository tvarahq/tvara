from .BaseTool import BaseTool
import sys
import io
import traceback

class CodeTool(BaseTool):
    def __init__(self, name: str = "code_tool", description: str = "Executes code snippets."):
        super().__init__(name=name, description=description)

    def run(self, input_data: str) -> str:
        stdout = io.StringIO()
        stderr = io.StringIO()
        local_vars = {}

        try:
            sys.stdout = stdout
            sys.stderr = stderr
            exec(input_data, local_vars, local_vars)
        except Exception:
            traceback.print_exc(file=stderr)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        out = stdout.getvalue().strip()
        err = stderr.getvalue().strip()

        if err:
            return f"Error: {err}"
        elif out:
            return f"Output: {out}"
        else:
            return "Code executed successfully, but no output was produced."