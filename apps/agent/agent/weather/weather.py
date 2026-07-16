import requests
import msgspec


class Location(msgspec.Struct):
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None
    timezone: str | None = None


class GeocodingResponse(msgspec.Struct):
    generationtime_ms: float
    results: list[Location] | None = None


class CurrentWeather(msgspec.Struct):
    time: str
    interval: int
    temperature_2m: float
    weather_code: int


class WeatherResponse(msgspec.Struct):
    latitude: float
    longitude: float
    generationtime_ms: float
    current: CurrentWeather


def fetch_city_data(query: str) -> GeocodingResponse:
    url = "http://geocoding-api.open-meteo.com/v1/search"
    data = {
            "name": query,
            "count": 1,
            "language": "en",
            "format": "json",
    }
    headers = {'User-Agent': 'WeatherTool/1.0'}

    response = requests.get(url, params=data, headers=headers)
    response.raise_for_status()
    result = msgspec.json.decode(response.text, type=GeocodingResponse)
    return result


def get_weather(lat: float, long: float) -> WeatherResponse:
    url = "https://api.open-meteo.com/v1/forecast"
    data = {
        "latitude": lat,
        "longitude": long,
        "current": "temperature_2m,weather_code",
        "timezone": "auto"
    }
    headers = {'User-Agent': 'WeatherTool/1.0'}

    response = requests.get(url, params=data, headers=headers)
    response.raise_for_status()
    return msgspec.json.decode(response.text, type=WeatherResponse)


if __name__ == "__main__":
    result = fetch_city_data("London")
    print(result)
    city = result.results[0]
    weather = get_weather(city.latitude, city.longitude)
    print(weather)
