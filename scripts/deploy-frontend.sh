#!/bin/bash
set -e

# Get environment from args or default to dev
ENVIRONMENT=${1:-dev}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|prod)$ ]]; then
    echo "Error: Environment must be either 'dev' or 'prod'"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo "Deploying to $ENVIRONMENT environment..."

# Build the Next.js app
cd src/frontend/funny-weather-ui
yarn install
yarn build

# Get the S3 bucket name from Terraform output
BUCKET_NAME=$(cd ../../../infrastructure && terraform output -raw frontend_bucket_name)

# Verify the bucket exists
if ! aws s3 ls "s3://$BUCKET_NAME" >/dev/null 2>&1; then
    echo "Error: Bucket $BUCKET_NAME does not exist"
    exit 1
fi

# Sync the build output to S3
aws s3 sync out/ s3://$BUCKET_NAME --delete

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(cd ../../../infrastructure && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"

echo "Frontend deployment complete for $ENVIRONMENT environment!"
echo "Website URL: $(cd ../../../infrastructure && terraform output -raw website_endpoint)"
echo "CloudFront URL: $(cd ../../../infrastructure && terraform output -raw cloudfront_domain_name)" 