from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather") 
# fastmcp enables the creation of MCP servers with minimal boilerplate code 
# through the use of decorators like @tool, @resource, and @prompt

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def get_weather_data(url: str) -> dict[str, Any] | None:
    """Define an asynchronous function that takes a URL and returns a dictionary or None"""
    # Define headers for the request
    headers = { 
        "User-Agent": USER_AGENT,   # Set the user agent (required by public APIs)
        "Accept": "application/geo+json", # Request GeoJSON format 
    }
    async with httpx.AsyncClient() as client: # Create an asynchronous HTTP client
        try: # Gracefully handle errors (e.g. network issues, timeouts, etc.)
            response = await client.get(url, headers=headers, timeout=35) # Send a GET request to the URL with the headers and timeout
            response.raise_for_status() # Check HTTP status code, 200-299, then nothing else raises httpx.HTTPStatusError
            return response.json() # Return the response as a dictionary
        
        # Return None if any other exception occurs
        except Exception: 
            return None

# Helper functions
def format_alert(feature: dict) -> str: 
    """Convert a weather alert dictionary to a string"""
    properties = feature["properties"] # Extract properties from the alert dictionary
    return f"""
Event: {properties.get('event', 'Unknown')}
Area: {properties.get('areaDesc', 'Unknown')}
Severity: {properties.get('severity', 'Unknown')}
Description: {properties.get('description', 'No Description')}
Instruction: {properties.get('instruction', 'No Specific Instruction')}
"""


# Impementing tool execution
@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    Get the weather alerts for a given state
    Args:
        state: 2 letter US state code example: "WA" for washington
    """
    
    url = f"{NWS_API_BASE}/alerts/active/area/{state}" # Build the URL for the alerts
    data = await get_weather_data(url) # Get the weather data asynchronously

    if not data or "features" not in data: # Check if the data is there and if "feature" key exists
        return "Unable to fetch alerts!"
    
    if not data["features"]: # Will be True if it’s an empty list
        return "No active alerts for this state"
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts) # Convert the alerts to a string


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    Get the forecast for a given location
    Args:
        latitude: latitude of the location
        longitude: longitude of the location
    """

    # Get the forcast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await get_weather_data(points_url)

    if not points_data:
        return "No Data Found"
    
    # Get the URL of forecast from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await get_weather_data(forecast_url)

    if not forecast_data:
        return "No Forecast Data Found"
    
    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"] 
    # properties contains metadata about the forecast and periods have time based entries 
    # with details like temp, wind etc.
    
    forecasts = []

    # Loops through the first 7 forecast periods (day/night chunks). Each period contains structured weather data.
    for period in periods[:7]:
        forecast =f"""
{period["name"]}:
Temperature: {period["temperature"]} Degrees {period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Precipitation: {period["probabilityOfPrecipitation"]["value"]}%
Detailed Forecast: {period["detailedForecast"]}"""

# Humidity: {period["relativeHumidity"]["value"]}%
# """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


if __name__ == "__main__":
    # This launches the MCP server we defined earlier with
    mcp.run(transport="stdio") # .run() starts the server and exposes the MCP tools
    # transport="stdio" means the server uill use standard IO to communicate with the LLM Client (e.g. Cursor IDE)