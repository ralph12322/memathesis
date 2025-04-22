#!/usr/bin/env bash

# Update package list and install system-level dependencies
apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    python3-dev \
    libsndfile1-dev \
    build-essential \
    libasound2-dev \
    libportaudio2

# Set up a virtual environment if you're not using one already
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
