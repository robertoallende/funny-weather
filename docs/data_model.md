# Funny Weather Data Model

## DynamoDB Table Design

### Table: funny_weather_entries

This table stores both weather data and generated jokes in a single entry for Wellington, New Zealand. The application currently supports only Wellington with fixed coordinates (-41.276825, 174.777969).

#### Key Structure
- **Partition Key**: `timestamp` (String, ISO format)
- **Sort Key**: `location` (String)

#### Attributes
- **weather_data** (Map)
  - coordinates (Map)
    - latitude (Number, fixed at -41.276825)
    - longitude (Number, fixed at 174.777969)
  - temperature (Number)
  - wind_speed (Number)
  - cloud_cover (Number)
  - visibility (Number)
  - precipitation (Number)
  - humidity (Number)

- **joke_data** (Map)
  - emoji (String)
  - weather_status (String)
  - jokes (List of Strings)

- **status** (String)
  - "PENDING" - Weather data stored, awaiting jokes
  - "COMPLETE" - Both weather and jokes are stored

- **ttl** (Number)
  - Unix timestamp for entry expiration
  - Set to 30 days after creation

#### Access Patterns
1. Get latest entry:
   ```
   Query by location with limit 1, sorted by timestamp DESC
   ```

2. Get historical data:
   ```
   Query by location with timestamp range
   ```

#### Data Retention
- Entries automatically deleted after 30 days via TTL
- Helps manage storage costs and data relevance

## IAM Permissions
The following permissions are required for Lambda functions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:Query",
                "dynamodb:GetItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/funny_weather_entries"
            ]
        }
    ]
}
``` 