import msgspec
import requests


class Location(msgspec.Struct):
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None
    timezone: str | None = None


class GeocodingResponse(msgspec.Struct):
    time: float = msgspec.field(name="generationtime_ms")
    results: list[Location] | None = None


class CurrentWeather(msgspec.Struct):
    time: str
    interval: int
    temperature: float = msgspec.field(name="temperature_2m")
    weather_code: int
    wind_speed: float = msgspec.field(name="wind_speed_10m")
    wind_direction: float = msgspec.field(name="wind_direction_10m")
    humidity: int = msgspec.field(name="relative_humidity_2m")


class WeatherResponse(msgspec.Struct):
    latitude: float
    longitude: float
    time: float = msgspec.field(name="generationtime_ms")
    current: CurrentWeather


def fetch_city_data(query: str) -> GeocodingResponse:
    url = "http://geocoding-api.open-meteo.com/v1/search"
    data = {
        "name": query,
        "count": 1,
        "language": "en",
        "format": "json",
    }
    headers = {"User-Agent": "WeatherTool/1.0"}

    response = requests.get(url, params=data, headers=headers)
    response.raise_for_status()
    result = msgspec.json.decode(response.text, type=GeocodingResponse)
    return result


def get_weather(city: str) -> WeatherResponse | None:
    result = fetch_city_data(city)
    if result.results:
        city = result.results[0]
        return get_weather_coord(city.latitude, city.longitude)


def get_weather_coord(lat: float, long: float) -> WeatherResponse:
    url = "https://api.open-meteo.com/v1/forecast"
    data = {
        "latitude": lat,
        "longitude": long,
        "current": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
        "timezone": "auto",
    }
    headers = {"User-Agent": "WeatherTool/1.0"}

    response = requests.get(url, params=data, headers=headers)
    response.raise_for_status()
    return msgspec.json.decode(response.text, type=WeatherResponse)


if __name__ == "__main__":
    result = fetch_city_data("London")
    print(result)
    if result.results:
        city = result.results[0]
        weather = get_weather_coord(city.latitude, city.longitude)
        print(weather)
