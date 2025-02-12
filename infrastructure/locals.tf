locals {
  tags = {
    Environment = var.environment
    Project     = "funny-weather"
    ManagedBy   = "terraform"
  }
} 