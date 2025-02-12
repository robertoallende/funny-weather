# Funny Weather

A cloud-native application that combines Wellington weather data with AI-generated humor. Get the capital's forecast with a side of laughter! 🌤️ 😄

<img width="613" alt="Screenshot 2025-02-13 at 11 21 24 AM" src="https://github.com/user-attachments/assets/0ba8c164-e736-4cb6-b6b6-ecb65448b1af" />

## Overview

Funny Weather is a microservices-based application that fetches real-time weather data for Wellington, New Zealand and generates contextual jokes based on the current conditions. It demonstrates modern cloud architecture practices using AWS services, combining serverless and containerized approaches.

### Key Features

- Real-time weather data integration
- AI-powered weather-themed joke generation
- Analytics dashboard for joke engagement metrics
- Responsive web interface
- RESTful API for service integration

### Tech Stack

- **Frontend**: React with Tailwind CSS
- **Backend Services**:
  - Python Lambda functions for weather data and joke generation
- **Infrastructure**: 
  - AWS (Lambda, DynamoDB)
  - Terraform for Infrastructure as Code
  - GitHub Actions for CI/CD
- **Monitoring**: AWS CloudWatch

## Local Development

### Prerequisites

- Python 3.9+
- Node.js 18+
- AWS CLI configured
- Docker
- Terraform

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/robertoallende/funny-weather
cd funny-weather
```

2. Set up local development environment:
```bash
./scripts/local-setup.sh
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Create a `terraform.tfvars` file in the `infrastructure` directory with the following variables:

```hcl
met_api_key = "your-metservice-api-key"
```

## Architecture
<img width="1805" alt="funny-weather-architecture" src="https://github.com/user-attachments/assets/d664b990-baa1-4482-8d44-8947cb41f357" />

The application follows a serverless architecture with:

- Frontend:
  - Next.js application hosted on S3 and served through CloudFront CDN
  - Single-page application design for optimal user experience

- Backend Services:
  - API Gateway as the central entry point for API requests
  - Multiple Lambda functions for specific responsibilities:
    - Weather Fetcher: Retrieves data from MetService API
    - Joke Generator: Integrates with OpenAI for content generation
    - Weather/Joke Storage: Handles data persistence
    - Get Weather API: Serves frontend requests

- Event-Driven Components:
  - EventBridge for scheduled weather fetching (1-hour intervals)
  - Event-based joke storage triggered by joke generation

- Data Storage:
  - DynamoDB table (funny-weather-entries) for storing weather and jokes
  - S3 for static frontend content

- External Integrations:
  - MetService API for weather data
  - OpenAI API for joke generation

This architecture prioritizes scalability, maintainability, and cost-effectiveness through serverless computing while ensuring reliable data processing and storage.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with weather data from MetService
- Uses OpenAI's API for joke generation
- Inspired by New Zealand's charming weather 🌦️

## Contact

For questions or feedback, please open an issue or reach out to [Roberto Allende](http://linkedin.com/in/robertoallende).

---
*Note: This project was initially created as a proof of concept to experiment with cloud-native development practices and serverless architecture.*

Built with ❤️ in Wellington, New Zealand
