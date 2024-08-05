#!/bin/bash

# Create and activate virtual environment
python -m venv antenv
source antenv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run the web app
gunicorn application:app
