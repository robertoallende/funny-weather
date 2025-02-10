import pytest
from src.lambdas.joke_generator.app import process_weather

def test_process_weather():
    # Test data
    weather_data = {
        'location': 'Wellington',
        'temperature': 288.15,  # 15°C
        'wind_speed': 5.0,
        'cloud_cover': 75.0,
        'visibility': 10000.0,
        'humidity': 85.0
    }
    
    # Process the weather data
    result = process_weather(weather_data)
    
    # Verify the result
    assert result['location'] == 'Wellington'
    assert result['temperature'] == 15.0  # Should be converted to Celsius
    assert result['wind_speed'] == 5.0
    assert result['cloud_cover'] == 75
    assert result['visibility'] == 10.0  # Should be converted to km
    assert result['humidity'] == 85 