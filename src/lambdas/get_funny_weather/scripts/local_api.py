from fastapi import FastAPI, HTTPException
import uvicorn
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Set environment variables for local testing
os.environ['LOCAL_DEVELOPMENT'] = 'true'
os.environ['DYNAMODB_TABLE'] = 'funny-weather-entries'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'

from app import handler

app = FastAPI()

@app.get("/weather")
async def get_weather():
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "local-123"
    
    # Call Lambda handler
    response = handler({}, MockContext())
    
    # Check response status code
    if response['statusCode'] != 200:
        raise HTTPException(
            status_code=response['statusCode'],
            detail=response['body']
        )
    
    # Return the response body
    return response['body']

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 