#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: ./run.sh <OPENAI_KEY>"
    exit 1
else
    export OPENAI_KEY=$1
fi

# Show the values being used
echo "Using OPENAI_KEY: $OPENAI_KEY"

# build and start Docker containers
docker-compose down
docker-compose build
docker-compose up -d

echo "Application is running at http://localhost:8080"
echo "Redis is running at localhost:6379"