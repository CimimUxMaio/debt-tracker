#!/bin/bash

IMAGE_NAME=$1
CONTAINER_NAME="${2:-$IMAGE_NAME}"

docker run --name $CONTAINER_NAME -d -v $(pwd)/data/:/app/data/ -v $(pwd)/.env:/app/.env $IMAGE_NAME
