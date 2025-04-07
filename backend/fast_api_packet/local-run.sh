#!/bin/bash

# Stop and remove any existing container
if [ $(docker ps -a -q -f name=fastapi-container) ]; then
    docker stop fastapi-container
    docker rm fastapi-container
fi

# Build the Docker image
docker build -t fastapi-app .

# Run the container
docker run --name fastapi-container -p 8080:8080 fastapi-app
