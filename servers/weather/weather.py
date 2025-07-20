from typing import Any
import httpx
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# Sample weather data for resources (you could make this dynamic)
SAMPLE_WEATHER_DATA = {
    "major_cities": {
        "New York": {"lat": 40.7128, "lon": -74.0060},
        "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
        "Chicago": {"lat": 41.8781, "lon": -87.6298},
        "Houston": {"lat": 29.7604, "lon": -95.3698},
        "Phoenix": {"lat": 33.4484, "lon": -112.0740}
    },
    "state_codes": {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming"
    }
}

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


# Add Resources
@mcp.resource("weather://cities")
async def get_major_cities() -> str:
    """List of major US cities with coordinates for weather lookups."""
    cities_info = []
    for city, coords in SAMPLE_WEATHER_DATA["major_cities"].items():
        cities_info.append(f"{city}: {coords['lat']}, {coords['lon']}")
    
    return "Major US Cities (Name: Latitude, Longitude):\n" + "\n".join(cities_info)

@mcp.resource("weather://states")  
async def get_state_codes() -> str:
    """US state codes and full names for weather alerts."""
    states_info = []
    for code, name in SAMPLE_WEATHER_DATA["state_codes"].items():
        states_info.append(f"{code}: {name}")
    
    return "US State Codes (Code: Full Name):\n" + "\n".join(states_info)

@mcp.resource("weather://api-info")
async def get_api_info() -> str:
    """Information about the National Weather Service API."""
    return f"""
National Weather Service API Information:

Base URL: {NWS_API_BASE}
User Agent: {USER_AGENT}

Available Endpoints:
- /alerts/active/area/{{state}} - Get active weather alerts for a state
- /points/{{lat}},{{lon}} - Get grid point data for coordinates
- /gridpoints/{{office}}/{{gridX}},{{gridY}}/forecast - Get forecast data

Usage Notes:
- All requests require a User-Agent header
- State codes should be 2-letter abbreviations (e.g., CA, NY)
- Coordinates should be within the United States
- API responses are in GeoJSON format

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


# Add Prompts
@mcp.prompt()
async def weather_report(location: str) -> str:
    """Create a comprehensive weather report for a location.
    
    Args:
        location: City name or 'latitude,longitude' coordinates
    """
    return f"""Please create a comprehensive weather report for {location}. 

Include the following:
1. Current weather alerts (if any)
2. Detailed forecast for the next few days
3. Any weather warnings or advisories
4. Summary of what people should expect and how to prepare

If the location is a city name, use the major cities resource to find coordinates. If it's a state, check for weather alerts first.
"""

@mcp.prompt()
async def severe_weather_analysis(state: str, timeframe: str = "today") -> str:
    """Analyze severe weather conditions for a state.
    
    Args:
        state: Two-letter US state code (e.g., CA, TX)
        timeframe: Time period to analyze (default: today)
    """
    return f"""Please analyze the severe weather situation for {state} for {timeframe}.

Provide:
1. All active weather alerts and their severity levels
2. Risk assessment for different types of severe weather
3. Recommendations for residents and travelers
4. Any emergency preparedness advice

Focus on the most critical threats and provide actionable guidance.
"""

@mcp.prompt()
async def travel_weather_advisory(origin: str, destination: str, travel_date: str = "today") -> str:
    """Create a travel weather advisory between two locations.
    
    Args:
        origin: Starting location (city name or coordinates)
        destination: Destination location (city name or coordinates)  
        travel_date: When you plan to travel (default: today)
    """
    return f"""Please create a travel weather advisory for a trip from {origin} to {destination} on {travel_date}.

Include:
1. Weather conditions at origin and destination
2. Any weather alerts along the route
3. Travel recommendations (delays, route changes, etc.)
4. What travelers should pack or prepare for
5. Best timing for departure if weather is a concern

Use both weather forecasts and active alerts to provide comprehensive travel guidance.
"""

@mcp.prompt()
async def emergency_weather_briefing(location: str) -> str:
    """Create an emergency weather briefing for emergency responders.
    
    Args:
        location: Location for the briefing (city, state, or coordinates)
    """
    return f"""Create an emergency weather briefing for {location} for emergency response teams.

Provide:
1. IMMEDIATE weather threats and alerts
2. Timeline of expected weather changes
3. Areas of highest concern/vulnerability
4. Resource deployment recommendations
5. Communication priorities for the public

Format this as a professional emergency briefing with clear, actionable information for first responders and emergency managers.
"""


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')