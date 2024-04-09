# vim: set ft=dockerfile :
FROM debian:latest

# Setup environment
RUN apt update && \
    apt upgrade -y && \
    apt install -y build-essential wget curl git

## Import Mozilla APT repository
RUN install -d -m 0755 /etc/apt/keyrings && \
    wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O- | tee /etc/apt/keyrings/packages.mozilla.org.asc > /dev/null && \
    echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" | tee -a /etc/apt/sources.list.d/mozilla.list > /dev/null && \
    apt update

## Install project dependencies
ENV GECKODRIVER_VERSION=v0.34.0
ARG GECKODRIVER_ARCH

RUN apt install -y firefox python3-poetry && \
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

