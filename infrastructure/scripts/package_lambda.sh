#!/bin/bash

set -e  # Exit on error

# Get absolute paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INFRA_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_DIR="$( cd "$INFRA_DIR/.." && pwd )"

# Get arguments
LAMBDA_NAME=$1
SOURCE_DIR="$PROJECT_DIR/src/lambdas/$LAMBDA_NAME"
BUILD_DIR="$INFRA_DIR/files/$LAMBDA_NAME/build"
OUTPUT_DIR="$INFRA_DIR/files/$LAMBDA_NAME"

echo "Starting Lambda packaging process..."
echo "Source directory: $SOURCE_DIR"
echo "Build directory: $BUILD_DIR"
echo "Output directory: $OUTPUT_DIR"

# Clean and create directories
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# Create a fresh virtual environment
echo "Creating virtual environment..."
python3 -m venv "$BUILD_DIR/venv"
source "$BUILD_DIR/venv/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install \
    --platform manylinux2014_x86_64 \
    --target="$BUILD_DIR" \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    -r "$SOURCE_DIR/requirements.txt"

# Copy lambda code
echo "Copying Lambda code..."
cp -r "$SOURCE_DIR"/* "$BUILD_DIR"/

# Remove unnecessary files
echo "Cleaning up..."
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} +
rm -rf "$BUILD_DIR/venv"
rm -f "$BUILD_DIR/requirements.txt"

# Create zip file
echo "Creating zip file..."
cd "$BUILD_DIR"
zip -r "$OUTPUT_DIR/$LAMBDA_NAME.zip" .

# Deactivate virtual environment
deactivate

echo "Verifying zip contents:"
unzip -l "$OUTPUT_DIR/$LAMBDA_NAME.zip" | grep -i numpy
unzip -l "$OUTPUT_DIR/$LAMBDA_NAME.zip" | grep -i "\.so$"

echo "Package created at $OUTPUT_DIR/$LAMBDA_NAME.zip"
