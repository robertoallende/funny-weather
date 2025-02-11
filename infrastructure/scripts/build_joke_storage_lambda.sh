#!/bin/bash
set -e

echo "Starting build script..."
echo "Current directory: $(pwd)"

# Set up variables
BUILD_DIR="build/joke_storage"
VENV_DIR="/tmp/lambda_venv_$(date +%s)_$$"  # Make venv directory unique with PID
SRC_DIR="../src/lambdas/joke_storage"

echo "Build directory: $(pwd)/${BUILD_DIR}"
echo "Virtual environment: ${VENV_DIR}"

# Create build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

echo "Installing dependencies..."
# Create new virtual environment
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

# Install dependencies into the build directory
pip install --platform manylinux2014_x86_64 --target "${BUILD_DIR}" --implementation cp --python-version 3.11 --only-binary=:all: \
    boto3 \
    aws-lambda-powertools \
    aws-xray-sdk

# Copy lambda function code
cp "${SRC_DIR}/app.py" "${BUILD_DIR}/"

# Clean up
deactivate
rm -rf "${VENV_DIR}"

echo "Build script completed."

# List contents of build directory
echo "Contents of build directory:"
ls -la "${BUILD_DIR}" 