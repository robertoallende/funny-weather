import pytest
import json
import os
from src.lambdas.get_funny_weather.app import handler

def test_get_weather_success(weather_table):
    """Test successful weather data retrieval."""
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler
    response = handler({}, MockContext())
    
    # Assert response structure
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    assert 'location' in body
    assert 'weather' in body
    assert 'joke' in body
    
    # Assert weather data
    weather = body['weather']
    assert 'temperature_celsius' in weather
    assert 'wind_speed' in weather
    assert 'cloud_cover' in weather
    assert 'visibility' in weather
    assert 'humidity' in weather
    
    # Assert joke data
    joke = body['joke']
    assert 'emoji' in joke
    assert 'weather_status' in joke
    assert 'jokes' in joke
    assert isinstance(joke['jokes'], list)

def test_get_weather_no_data(weather_table):
    """Test when no weather data is available."""
    # Clear the table
    weather_table.delete_item(
        TableName='funny-weather-entries',
        Key={
            'location': {'S': 'Wellington'},
            'timestamp': {'S': weather_table.scan(TableName='funny-weather-entries')['Items'][0]['timestamp']['S']}
        }
    )
    
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler
    response = handler({}, MockContext())
    
    # Assert response
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body

def test_get_weather_missing_table(mock_dynamodb_service):
    """Test when DynamoDB table doesn't exist."""
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler without creating table
    response = handler({}, MockContext())
    
    # Assert response
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body

def test_get_weather_missing_env_var(weather_table):
    """Test when environment variable is missing."""
    # Remove required environment variable
    del os.environ['DYNAMODB_TABLE']
    
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler
    response = handler({}, MockContext())
    
    # Assert response
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body
    
    # Restore environment variable
    os.environ['DYNAMODB_TABLE'] = 'funny-weather-entries' 