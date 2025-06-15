#!/bin/bash
# Variables for container name and image name
CONTAINER_NAME="fastapi-container"
IMAGE_NAME="fastapi-image"


# Check if Dockerfile exists
if [ ! -f Dockerfile ]; then
    echo "Dockerfile not found. Please make sure it's in the current directory."
    exit 1
fi


# Remove any running or stopped containers with the same name
if [ $(docker ps -a -q -f name=$CONTAINER_NAME) ]; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Remove any existing images with the same name
if [ $(docker images -q $IMAGE_NAME) ]; then
    echo "Removing existing image..."
    docker rmi $IMAGE_NAME
fi

# Build the new Docker image
echo "Building new Docker image..."
docker build -t $IMAGE_NAME .

# Run the container
docker run --name $CONTAINER_NAME \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
    -it -p 8080:8080 $IMAGE_NAME
