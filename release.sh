#!/bin/bash

# Get the latest git tag
TAG=$(git describe --tags --abbrev=0)

# Check if tag was found
if [ -z "$TAG" ]; then
  echo "No git tag found. Please create a tag first."
  exit 1
fi

# Docker image name
IMAGE="fra.vultrcr.com/botscave/laera_islenska:$TAG"

# Show the current tag and ask whether to build
echo "Current git tag: $TAG"
read -p "Do you want to build the Docker image '$IMAGE'? (y/N): " BUILD_CONFIRM
if [[ ! "$BUILD_CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Build canceled."
  exit 0
fi

# Build the Docker image
echo "Building Docker image: $IMAGE"
docker buildx build --platform=linux/amd64 . -t "$IMAGE"

# Ask for confirmation before pushing
read -p "Do you want to push the image '$IMAGE'? (y/N): " PUSH_CONFIRM
if [[ "$PUSH_CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Pushing Docker image: $IMAGE"
  docker push "$IMAGE"
else
  echo "Push canceled."
fi
