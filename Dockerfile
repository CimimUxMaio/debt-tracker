# vim: set ft=dockerfile :
FROM debian:latest

# Setup environment
RUN apt update && \
    apt upgrade -y && \
    apt install -y build-essential wget curl git

## Install project dependencies
RUN apt install -y firefox-esr python3-poetry

## Install geckodriver
ARG GECKODRIVER_VERSION=v0.34.0

RUN GECKODRIVER_ARCH=$([ "$(uname -m)" = "x86_64" ] && echo "linux64" || ([ "$(uname -m)" = "aarch64" ] && echo "linux-aarch64")) && \
    if [ -z "$GECKODRIVER_ARCH" ]; then echo "Unsupported architecture"; exit 1; fi && \
    echo "GECKODRIVER_ARCH = $GECKODRIVER_ARCH" && \
    wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-$GECKODRIVER_ARCH.tar.gz && \
    tar -xvzf geckodriver-$GECKODRIVER_VERSION-$GECKODRIVER_ARCH.tar.gz && \
    chmod +xrw geckodriver && \
    mv geckodriver /usr/local/bin

# Project setup
WORKDIR /app
COPY pyproject.toml .
RUN poetry install --no-root
COPY . .

CMD ["poetry", "run", "python", "src/main.py"]

