#!/bin/bash

# Install dependencies
pip install -r ../requirements.txt

# Insert test data
python setup_test_data.py

# Start the local API server
python local_api.py 