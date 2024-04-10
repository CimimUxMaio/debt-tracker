#!/bin/bash

IMAGE_NAME=$1
CONTAINER_NAME="${2:-$IMAGE_NAME}"

OPTIONS="--name $CONTAINER_NAME -v $(pwd)/data/:/app/data/ --env-file .env"
if ! [ -z "$3" ]; then
    if [ "$3" == "--bash" ]; then
        echo "Running bash in interactive mode."
        OPTIONS="$OPTIONS --rm -it"
        COMMAND=bash
    else
        echo "Unknown option: $3" 1>&2
        exit 1
    fi
else
    echo "Running application in detached mode."
    OPTIONS="$OPTIONS -d"
fi

docker run $OPTIONS $IMAGE_NAME $COMMAND
