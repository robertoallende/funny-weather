# DynamoDB table for weather entries
resource "aws_dynamodb_table" "weather_entries" {
  name           = "funny-weather-entries"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "location"
  range_key      = "timestamp"

  attribute {
    name = "location"
    type = "S"
  }

  attribute {
    name = "timestamp"
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

# Add this after the table resource
resource "null_resource" "insert_test_data" {
  depends_on = [aws_dynamodb_table.weather_entries]

  provisioner "local-exec" {
    command = "python3 scripts/insert_test_data.py"
    working_dir = path.module
  }

  triggers = {
    table_name = aws_dynamodb_table.weather_entries.name
  }
} 