from datetime import datetime
from zoneinfo import ZoneInfo

from agentscope.tool import Toolkit
from agentscope.tool import ToolResponse

def get_current_time() -> ToolResponse:
      """Get the local time of the current machine.

      Args:
          None
      """
      now = str(datetime.now())
      
      return ToolResponse(content=[{"type": "text", "text": now}])



def register_current_time_tools(toolkit: Toolkit) -> None:
    toolkit.register_tool_function(get_current_time)
    

