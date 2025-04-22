#!/usr/bin/env bash

# Update package list and install system-level dependencies
apt-get update && apt-get install -y portaudio19-dev gcc python3-dev

# Optional: Install any other system-level dependencies you might need
# apt-get install -y <other-packages>

# Set up a virtual environment if you're not using one already
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Optional: Run any additional commands (e.g., testing, migrations, etc.)
# python manage.py migrate  # If using Django, for example
