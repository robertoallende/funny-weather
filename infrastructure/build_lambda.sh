#!/bin/bash
set -e

# Create a temporary directory for building the package
BUILD_DIR="$(pwd)/build/weather_fetcher"

# Clean existing files but keep directory
rm -rf $BUILD_DIR/*

# Install dependencies into the build directory
pip install -r ../src/lambdas/weather_fetcher/requirements.txt -t $BUILD_DIR/

# Copy lambda source code
cp -r ../src/lambdas/weather_fetcher/*.py $BUILD_DIR/

# Clean up unnecessary files
find $BUILD_DIR -type d -name "__pycache__" -exec rm -rf {} +
find $BUILD_DIR -type f -name "*.pyc" -delete
find $BUILD_DIR -type f -name "*.pyo" -delete
find $BUILD_DIR -type f -name "*.pyd" -delete

# Create the deployment package directory if it doesn't exist
mkdir -p files