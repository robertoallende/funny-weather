#!/bin/bash
set -e

echo "Starting build script..."
echo "Current directory: $(pwd)"

# Create a temporary directory for building the package
BUILD_DIR="$(pwd)/build/joke_generator"
# Use a unique temp directory name with timestamp and PID
VENV_DIR="/tmp/lambda_venv_$(date +%s)_$$"

echo "Build directory: $BUILD_DIR"
echo "Virtual environment: $VENV_DIR"

# Clean existing files but keep directory
rm -rf $BUILD_DIR/*

echo "Installing dependencies..."
# Clean up any existing virtual environment and create new one
rm -rf "${VENV_DIR}" || true
python -m venv "${VENV_DIR}" || {
    echo "Failed to create virtual environment, trying to clean up..."
    rm -rf "${VENV_DIR}"
    python -m venv "${VENV_DIR}"
}

source "${VENV_DIR}/bin/activate"

# Install dependencies into the build directory
pip install --platform manylinux2014_x86_64 --target $BUILD_DIR --implementation cp --python-version 3.11 --only-binary=:all: \
    openai \
    python-dotenv \
    aws-lambda-powertools \
    aws-xray-sdk \
    boto3

# Deactivate virtual environment
deactivate

# Clean up virtual environment
rm -rf "${VENV_DIR}" || true

echo "Copying source files..."
# Copy lambda source code
cp -r ../src/lambdas/joke_generator/*.py $BUILD_DIR/

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