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
        # Get location coordinates from event
        location = event.get("location", "Wellington")  # Default to Wellington
        
        # Hardcoded coordinates for now - in production would use a location lookup service
        coordinates = {
            "Wellington": (-41.276825, 174.777969),
            # Add more NZ cities as needed
        }
        
        if location not in coordinates:
            raise ValueError(f"Location {location} not supported")
            
        lat, lon = coordinates[location]

        # Initialize MetOcean client
        api_key = environ.get("MET_API_KEY")
        if not api_key:
            logger.error("MET_API_KEY environment variable is not set")
            raise ValueError("MET_API_KEY environment variable is not set. Please configure the API key in your environment variables.")
        
        client = MetOceanClient(api_key)
        
        # Fetch weather data
        raw_weather_data = client.get_current_weather(lat, lon)
        
        # Process weather data
        weather_response = process_weather_data(raw_weather_data, location)
        
        return {
            "statusCode": 200,
            "body": json.dumps(weather_response.model_dump())
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }