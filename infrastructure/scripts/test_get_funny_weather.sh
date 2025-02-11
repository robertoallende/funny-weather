#!/bin/bash

# Change to the infrastructure directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if needed
pip install -r requirements.txt

# Run the test script
python scripts/test_lambda.py

# Deactivate virtual environment
deactivate 