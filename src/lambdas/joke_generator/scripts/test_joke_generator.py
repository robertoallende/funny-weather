import sys
import os
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import generate_content

def test_joke_generator():
    """Test the joke generator with sample weather data"""
    test_data = {
        "location": "Wellington",
        "temperature": 288.10434,
        "wind_speed": 5.2222743,
        "cloud_cover": 52.080406,
        "visibility": 40538.406,
        "precipitation": 0.004236678,
        "humidity": 84.70121,
        "timestamp": "2025-02-06T09:32:51.251828+00:00"
    }
    
    print("Testing joke generator with sample weather data...")
    result = generate_content(test_data)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_joke_generator()