# DynamoDB table for weather entries
resource "aws_dynamodb_table" "weather_entries" {
  name           = "funny_weather_entries"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "timestamp"
  range_key      = "location"

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "location"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled       = true
  }

  tags = {
    Environment = "production"
    Project     = "funny-weather"
  }
}

# IAM policy for Lambda functions to access DynamoDB
resource "aws_iam_policy" "dynamodb_access" {
  name        = "funny-weather-dynamodb-access"
  description = "IAM policy for accessing funny weather DynamoDB table"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:GetItem"
        ]
        Resource = [
          aws_dynamodb_table.weather_entries.arn
        ]
      }
    ]
  })
}

# Attach DynamoDB policy to existing Lambda role
resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  policy_arn = aws_iam_policy.dynamodb_access.arn
  role       = aws_iam_role.lambda_role.name
} 