# EventBridge Schedule for Weather Fetcher
resource "aws_scheduler_schedule" "weather_fetch_schedule" {
  name       = "weather-fetch-schedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 hour)"

  target {
    arn      = aws_lambda_function.weather_fetcher.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# IAM Role for EventBridge Scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "weather-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

# Policy for EventBridge Scheduler
resource "aws_iam_role_policy" "scheduler_policy" {
  name = "weather-scheduler-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.weather_fetcher.arn
        ]
      }
    ]
  })
}

# EventBridge Rule for Weather Events
resource "aws_cloudwatch_event_rule" "weather_fetched" {
  name        = "weather-fetched-rule"
  description = "Capture WeatherFetched events"

  event_pattern = jsonencode({
    source      = ["custom.funnyweather"]
    detail-type = ["WeatherFetched"]
  })
}

# EventBridge Target for Joke Generator
resource "aws_cloudwatch_event_target" "joke_generator" {
  rule      = aws_cloudwatch_event_rule.weather_fetched.name
  target_id = "JokeGeneratorTarget"
  arn       = aws_lambda_function.joke_generator.arn
}

# Allow EventBridge to invoke Joke Generator Lambda
resource "aws_lambda_permission" "allow_eventbridge_joke_generator" {
  statement_id  = "AllowEventBridgeInvokeJokeGenerator"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.joke_generator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weather_fetched.arn
}