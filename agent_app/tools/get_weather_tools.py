import requests
from agentscope.tool import Toolkit
from agentscope.tool import ToolResponse

CITY_MAP = {
    "成都双流区": "成都",
}

def get_weather(location: str = "成都") -> ToolResponse:
    """Get the local time of the current machine.

        Args:
            None
      """
    city = CITY_MAP.get(location, location)

    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        current = data["current_condition"][0]
        weather = current["weatherDesc"][0]["value"]
        temp = current["temp_C"]
        humidity = current["humidity"]
        wind = current["windspeedKmph"]

        return ToolResponse(
            content=[
                {
                    "type": "text",
                    "text": (
                        f"{location}当前天气：{weather}，"
                        f"温度 {temp}°C，湿度 {humidity}%，风速 {wind} km/h。"
                    ),
                }
            ],
            metadata={
                "location": location,
                "resolved_city": city,
                "temp": temp,
                "weather": weather,
                "humidity": humidity,
                "wind": wind,
            },
        )

    except Exception as e:
        return ToolResponse(
            content=[
                {
                    "type": "text",
                    "text": f"查询 {location} 天气失败：{e}",
                }
            ],
            metadata={
                "location": location,
                "resolved_city": city,
                "error": str(e),
            },
        )
    
def register_get_weather_tools(toolkit: Toolkit) -> None:
    toolkit.register_tool_function(get_weather)
