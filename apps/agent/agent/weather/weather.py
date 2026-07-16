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


if __name__ == "__main__":
    result = fetch_city_data("London")
    print(result)
