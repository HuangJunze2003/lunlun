from agentscope.tool import Toolkit

from agent_app.tools.code_tools import register_code_tools
from agent_app.tools.get_current_time import register_current_time_tools
from agent_app.tools.get_weather_tools import register_get_weather_tools


def build_toolkit() -> Toolkit:
    toolkit = Toolkit()
    register_code_tools(toolkit)
    register_current_time_tools(toolkit)
    register_get_weather_tools(toolkit)
    return toolkit