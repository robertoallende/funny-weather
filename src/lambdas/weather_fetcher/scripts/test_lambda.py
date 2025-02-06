import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app import handler
from os import environ
import json

def main():
    # Mock event that would come from API Gateway
    test_event = {
        "location": "Wellington"
    }
    
    # Mock Lambda context (not used in our handler but required for Lambda interface)
    class MockContext:
        def __init__(self):
            self.function_name = "weather_fetcher"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:weather_fetcher"
            self.aws_request_id = "local-123"
    
    # Call the handler
    response = handler(test_event, MockContext())
    
    # Print the response as formatted JSON
    print("\nLambda Response:")
    print(json.dumps({
        "statusCode": response["statusCode"],
        "body": json.loads(response["body"])  # Parse the JSON string back to object
    }, indent=2))

if __name__ == "__main__":
    main()