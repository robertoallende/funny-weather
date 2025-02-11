#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt

# Insert test data
python setup_test_data.py

# Start the local API server
python local_api.py 