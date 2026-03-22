from agentscope.tool import Toolkit, execute_python_code


def register_code_tools(toolkit: Toolkit) -> None:
    toolkit.register_tool_function(execute_python_code)