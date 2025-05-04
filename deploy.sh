#!/bin/bash

# Bybit Alert Bot deployment script
# This script builds and deploys the bot

set -e  # Exit on error

# Create required directories if they don't exist
mkdir -p data logs

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please create a .env file based on .env.example"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

# Stop any existing container
echo "Stopping any existing containers..."
docker-compose down || true

# Build the new image
echo "Building new Docker image..."
docker-compose build

# Start the container
echo "Starting the bot..."
docker-compose up -d

echo "Deployment complete!"
echo "Check logs with: docker-compose logs -f" 