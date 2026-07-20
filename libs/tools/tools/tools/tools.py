def get_weather(city: str) -> str:
    """
    Fetches the current weather for a specific city.
    """
    if "london" in city.lower():
        return "15°C and cloudy"
    return "22°C and sunny"
