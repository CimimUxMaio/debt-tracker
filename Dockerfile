# vim: set ft=dockerfile :
FROM archlinux:latest

# Setup environment
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm base-devel wget curl git

RUN pacman -S --noconfirm firefox geckodriver python-poetry

# Project setup
WORKDIR /app
COPY pyproject.toml .
RUN poetry install --no-root
COPY . .

CMD ["poetry", "run", "python", "src/main.py"]
