import pytest
from src.lambdas.weather_fetcher.app import process_weather_data, WeatherResponse

def test_process_weather_data():
    # Test data
    raw_data = {
        "variables": {
            "air.temperature.at-2m": {
                "data": [288.15],  # 15°C
                "noData": [False]
            },
            "wind.speed.at-10m": {
                "data": [5.0],
                "noData": [False]
            },
            "cloud.cover": {
                "data": [75.0],
                "noData": [False]
            },
            "air.visibility": {
                "data": [10000.0],
                "noData": [False]
            },
            "precipitation.rate": {
                "data": [0.0],
                "noData": [False]
            },
            "air.humidity.at-2m": {
                "data": [85.0],
                "noData": [False]
            }
        }
    }
    
    location = "Wellington"
    
    # Process the data
    result = process_weather_data(raw_data, location)
    
    # Verify the result is a WeatherResponse
    assert isinstance(result, WeatherResponse)
    assert result.location == "Wellington"
    assert isinstance(result.temperature, float)
    assert isinstance(result.wind_speed, float)
    assert isinstance(result.cloud_cover, float)
    assert isinstance(result.visibility, float)
    assert isinstance(result.humidity, float) 