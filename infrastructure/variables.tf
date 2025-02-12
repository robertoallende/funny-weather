variable "met_api_key" {
  description = "API key for MetService API"
  type        = string
}

variable "openai_api_key" {
  description = "API key for OpenAI API"
  type        = string
}

variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'."
  }
}

variable "frontend_domain" {
  description = "Domain name for the frontend"
  type        = string
  default     = ""
} 