#!/bin/bash
set -e

echo "Starting build script..."
echo "Current directory: $(pwd)"

# Create a temporary directory for building the package
BUILD_DIR="$(pwd)/build/weather_storage"
echo "Build directory: $BUILD_DIR"

# Clean existing files but keep directory
rm -rf $BUILD_DIR/*

echo "Installing dependencies..."
# Create and activate a temporary virtual environment
python -m venv /tmp/lambda_venv
source /tmp/lambda_venv/bin/activate

# Install dependencies into the build directory
pip install --platform manylinux2014_x86_64 --target $BUILD_DIR --implementation cp --python-version 3.11 --only-binary=:all: \
    boto3 \
    aws-lambda-powertools \
    aws-xray-sdk

# Deactivate virtual environment
deactivate

# Clean up virtual environment
rm -rf /tmp/lambda_venv

echo "Copying source files..."
# Copy lambda source code
cp -r ../src/lambdas/weather_storage/*.py $BUILD_DIR/

echo "Cleaning up unnecessary files..."
# Clean up unnecessary files
find $BUILD_DIR -type d -name "__pycache__" -exec rm -rf {} +
find $BUILD_DIR -type f -name "*.pyc" -delete
find $BUILD_DIR -type f -name "*.pyo" -delete
find $BUILD_DIR -type f -name "*.pyd" -delete
find $BUILD_DIR -type d -name "tests" -exec rm -rf {} +
find $BUILD_DIR -type d -name "testing" -exec rm -rf {} +

echo "Build script completed."

# List contents of build directory
echo "Contents of build directory:"
ls -la $BUILD_DIR 