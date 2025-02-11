# app.py
import json
from openai import OpenAI
from os import environ
from aws_lambda_powertools import Logger, Tracer
import boto3
import os

# Only enable tracing if not in local development
if not os.environ.get('LOCAL_DEVELOPMENT'):
    from aws_xray_sdk.core import patch_all
    patch_all()

logger = Logger()
tracer = Tracer()

def get_openai_client():
    """Get OpenAI client instance"""
    try:
        api_key = environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Log first few characters of API key to verify it's set (but not the whole key)
        logger.info(f"OpenAI API key found (starts with: {api_key[:4]}...)")
        
        client = OpenAI(api_key=api_key)
        
        # Test the client with a simple request
        try:
            client.models.list()
            logger.info("Successfully tested OpenAI client")
        except Exception as e:
            logger.error(f"Failed to test OpenAI client: {str(e)}")
            raise
            
        return client
        
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {str(e)}")
        raise

def kelvin_to_celsius(kelvin):
    """Convert Kelvin to Celsius"""
    return round(kelvin - 273.15, 1)

def process_weather(weather_data):
    """Process and format weather data for the prompt"""
    logger.info("Processing weather data", extra={"weather_data": weather_data})
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
        logger.info("Formatted weather data", extra={"formatted_weather": formatted_weather})
        
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

        logger.info("Sending request to OpenAI", extra={"prompt": prompt})
        
        try:
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
            logger.info("Received response from OpenAI")
            
            content = response.choices[0].message.content.strip()
            logger.info("Parsing OpenAI response", extra={"content": content})
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise ValueError(f"OpenAI API error: {str(e)}")

    except Exception as e:
        logger.error(f"Error in generate_content: {str(e)}")
        return {
            "error": str(e)
        }

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for joke generator
    """
    try:
        logger.info("Starting joke generation", extra={"event": event})
        
        # Extract weather data from event
        if 'detail' in event:
            weather_data = event['detail']
        else:
            weather_data = json.loads(event.get('body', '{}'))
        
        logger.info("Extracted weather data", extra={"weather_data": weather_data})
        
        # Verify required fields are present
        required_fields = ['location', 'temperature', 'wind_speed', 'cloud_cover', 'visibility', 'humidity']
        missing_fields = [field for field in required_fields if field not in weather_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Generate content based on weather data
        try:
            content = generate_content(weather_data)
            logger.info("Generated content", extra={"content": content})
            
            if "error" in content:
                raise ValueError(f"Error generating content: {content['error']}")
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise
        
        # Create EventBridge client
        events = boto3.client('events')
        
        # Put event for joke storage
        try:
            event_detail = {
                'timestamp': weather_data['timestamp'],
                'location': weather_data['location'],
                'body': json.dumps(content)
            }
            logger.info("Publishing event", extra={"event_detail": event_detail})
            
            response = events.put_events(
                Entries=[{
                    'Source': 'custom.funnyweather',
                    'DetailType': 'JokeGenerated',
                    'Detail': json.dumps(event_detail)
                }]
            )
            logger.info("Successfully published joke event", extra={"response": response})
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
            raise
        
        return {
            "statusCode": 200,
            "body": json.dumps(content)
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }