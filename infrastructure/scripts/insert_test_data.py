import boto3
from datetime import datetime, timezone
import time

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='ap-southeast-2',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def wait_for_table(table_name, max_attempts=10):
    for i in range(max_attempts):
        try:
            dynamodb.describe_table(TableName=table_name)
            print(f"Table {table_name} is ready")
            return True
        except Exception as e:
            print(f"Waiting for table... ({i+1}/{max_attempts})")
            time.sleep(2)
    return False

# Test data
test_item = {
    'timestamp': {'S': datetime.now(timezone.utc).isoformat()},
    'location': {'S': 'Wellington'},
    'weather_data': {'M': {
        'temperature': {'N': '288.15'},  # 15°C
        'wind_speed': {'N': '25.0'},
        'cloud_cover': {'N': '75'},
        'visibility': {'N': '10000'},
        'humidity': {'N': '85'}
    }},
    'joke_data': {'M': {
        'emoji': {'S': '🌧️'},
        'weather_status': {'S': 'Windy with light rain'},
        'jokes': {'L': [
            {'S': 'Why did the weather report go to therapy? It was dealing with too many cloudy issues!'}
        ]}
    }},
    'status': {'S': 'COMPLETE'}
}

# Wait for table to be ready
if not wait_for_table('funny-weather-entries'):
    print("Table not ready, exiting")
    exit(1)

try:
    # Verify table exists
    tables = dynamodb.list_tables()
    print(f"Available tables: {tables['TableNames']}")
    
    # Insert test data
    response = dynamodb.put_item(
        TableName='funny-weather-entries',
        Item=test_item
    )
    print(f"Put item response: {response}")
    
    # Verify data was inserted
    scan_result = dynamodb.scan(TableName='funny-weather-entries')
    print(f"Scan result: {scan_result}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    raise 