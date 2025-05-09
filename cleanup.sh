#!/bin/bash

# Get the project name from docker-compose (default to folder name)
PROJECT_NAME=$(basename "$(pwd)")

# Stop and remove only the containers and networks related to this compose file
echo "Stopping Docker Compose services for project: $PROJECT_NAME"
docker-compose down --remove-orphans

# Remove only volumes specific to this Compose project
echo "Removing Docker Compose volumes..."
docker volume rm $(docker volume ls -qf "name=${PROJECT_NAME}_*")

# Remove only networks specific to this Compose project
echo "Removing Docker Compose networks..."
docker network rm $(docker network ls -q --filter "name=${PROJECT_NAME}_*")

echo "Cleanup completed for project: $PROJECT_NAME"