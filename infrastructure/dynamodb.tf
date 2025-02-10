# DynamoDB table for weather and joke entries
resource "aws_dynamodb_table" "funny_weather_entries" {
  name           = "funny-weather-entries"
  billing_mode   = "PAY_PER_REQUEST"  # On-demand capacity
  hash_key       = "timestamp"
  range_key      = "location"

  attribute {
    name = "timestamp"
    type = "S"  # String
  }

  attribute {
    name = "location"
    type = "S"  # String
  }

  ttl {
    attribute_name = "ttl"
    enabled       = true
  }

  tags = {
    Environment = "development"
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
          aws_dynamodb_table.funny_weather_entries.arn
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