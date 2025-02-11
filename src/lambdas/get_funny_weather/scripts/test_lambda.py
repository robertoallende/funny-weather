import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
from app import handler
import json

def main():
    # Set environment variables for testing
    os.environ['DYNAMODB_TABLE'] = 'funny-weather-entries'
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
    
    # Configure boto3 to use LocalStack
    os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
    
    # Mock event
    test_event = {}
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "local-123"
    
    # Call handler
    response = handler(test_event, MockContext())
    
    # Print response
    print("\nLambda Response:")
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main() 