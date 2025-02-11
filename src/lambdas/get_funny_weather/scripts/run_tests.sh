#!/bin/bash

# Change to the lambda function directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies
pip install -r requirements.txt

# Add project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(git rev-parse --show-toplevel)

# Run tests with coverage config
pytest tests/ -v --cov=. --cov-config=.coveragerc 