import os
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
from os import environ

import numpy as np
from numpy.ma import masked_array
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel
import boto3

logger = Logger()
tracer = Tracer()

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    wind_speed: float
    cloud_cover: float
    visibility: float
    precipitation: float
    humidity: float
    timestamp: str

class MetOceanClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://forecast-v2.metoceanapi.com/point/time"
        self.headers = {
            "x-api-key": api_key
        }
    
    @tracer.capture_method
    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch current weather data for given coordinates in New Zealand
        """
        try:
            json_data = {
                "points": [{
                    "lon": lon,
                    "lat": lat
                }],
                "variables": [
                    "air.temperature.at-2m",
                    "wind.speed.at-10m",
                    "cloud.cover",
                    "air.visibility",
                    "precipitation.rate",
                    "air.humidity.at-2m"
                ],
                "time": {
                    "from": f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}",
                    "interval": "3h",
                    "repeat": 1
                }
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=json_data
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise

def process_weather_data(raw_data: Dict[str, Any], location: str) -> WeatherResponse:
    """
    Process raw weather data into a standardized format
    """
    def get_masked_value(variable_data: Dict[str, List], default: float = 0.0) -> float:
        if not variable_data or 'data' not in variable_data:
            return default
        masked = masked_array(
            variable_data["data"], 
            mask=variable_data["noData"], 
            dtype=np.float64
        )
        return float(masked[0]) if masked.size > 0 else default

    variables = raw_data.get("variables", {})
    
    return WeatherResponse(
        location=location,
        temperature=get_masked_value(variables.get("air.temperature.at-2m")),
        wind_speed=get_masked_value(variables.get("wind.speed.at-10m")),
        cloud_cover=get_masked_value(variables.get("cloud.cover")),
        visibility=get_masked_value(variables.get("air.visibility")),
        precipitation=get_masked_value(variables.get("precipitation.rate")),
        humidity=get_masked_value(variables.get("air.humidity.at-2m")),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler to fetch and process weather data
    """
    try:
        logger.info("Starting weather fetch", extra={"event": event})
        
        # Get location coordinates from event
        location = event.get("location", "Wellington")  # Default to Wellington
        logger.info(f"Processing location: {location}")
        
        # Hardcoded coordinates for now
        coordinates = {
            "Wellington": (-41.276825, 174.777969),
        }
        
        if location not in coordinates:
            logger.error(f"Location not supported: {location}")
            raise ValueError(f"Location {location} not supported")
            
        lat, lon = coordinates[location]
        logger.info(f"Using coordinates: {lat}, {lon}")

        # Initialize MetOcean client using environment variable
        met_api_key = os.environ['MET_API_KEY']
        client = MetOceanClient(met_api_key)
        
        # Fetch weather data
        try:
            raw_weather_data = client.get_current_weather(lat, lon)
            logger.info("Successfully fetched weather data")
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {str(e)}")
            raise
        
        # Process weather data
        weather_response = process_weather_data(raw_weather_data, location)
        logger.info("Successfully processed weather data")
        
        # Create EventBridge client
        events = boto3.client('events')
        
        # Put event for weather storage
        try:
            event_detail = weather_response.model_dump()
            logger.info("Publishing event", extra={"event_detail": event_detail})
            
            response = events.put_events(
                Entries=[{
                    'Source': 'custom.funnyweather',
                    'DetailType': 'WeatherFetched',
                    'Detail': json.dumps(event_detail)
                }]
            )
            logger.info("Successfully published event", extra={"response": response})
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
            raise
        
        return {
            "statusCode": 200,
            "body": json.dumps(weather_response.model_dump())
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }