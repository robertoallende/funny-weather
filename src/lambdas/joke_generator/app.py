# app.py
import json
from openai import OpenAI
from os import environ

def get_openai_client():
    """Get OpenAI client instance"""
    api_key = environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please configure the API key in your environment variables.")
    return OpenAI(api_key=api_key)

def kelvin_to_celsius(kelvin):
    """Convert Kelvin to Celsius"""
    return round(kelvin - 273.15, 1)

def process_weather(weather_data):
    """Process and format weather data for the prompt"""
    return {
        'location': weather_data['location'],
        'temperature': kelvin_to_celsius(weather_data['temperature']),
        'wind_speed': round(weather_data['wind_speed'], 1),
        'cloud_cover': round(weather_data['cloud_cover']),
        'visibility': round(weather_data['visibility'] / 1000, 1),  # to km
        'humidity': round(weather_data['humidity'])
    }

def generate_content(weather_data):
    """Generate weather content using OpenAI"""
    try:
        client = get_openai_client()
        formatted_weather = process_weather(weather_data)
        
        # Create the prompt without using f-string for the JSON structure
        weather_conditions = f"""
        Temperature: {formatted_weather['temperature']}°C
        Wind Speed: {formatted_weather['wind_speed']} m/s
        Cloud Cover: {formatted_weather['cloud_cover']}%
        Visibility: {formatted_weather['visibility']} km
        Humidity: {formatted_weather['humidity']}%
        """
        
        prompt = f"""Given these weather conditions for {formatted_weather['location']}:
{weather_conditions}

Generate a JSON response with:
1. A single emoji representing the weather
2. A short weather status (maximum five words)
3. Ten weather-related jokes

Make the jokes contextual and reference:
- The temperature
- Wind conditions (Wellington is known as 'Windy Wellington')
- Cloud cover or visibility
- The humidity level

Keep the humor lighthearted and celebrate Wellington's unique weather.

The response should be a valid JSON object with exactly these three fields:
- emoji: a single weather emoji
- weather_status: a short status (max 5 words)
- jokes: an array of exactly 10 strings

Make sure to return only the JSON, no additional text."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a weather-aware content creator specialized in New Zealand weather humor. 
                    Always respond with valid JSON containing exactly three fields: 
                    'emoji' (string), 'weather_status' (string), and 'jokes' (array of 10 strings)."""
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        return json.loads(response.choices[0].message.content.strip())

    except Exception as e:
        return {
            "error": str(e)
        }

def handler(event, context):
    """
    Lambda handler for joke generator
    """
    try:
        # Generate content based on weather data
        content = generate_content(event)
        
        return {
            "statusCode": 200,
            "body": json.dumps(content)
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }