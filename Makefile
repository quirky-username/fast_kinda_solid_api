# Define variables
DOCKER_COMPOSE = docker-compose
DOCKER_IMAGE_NAME = test-postgres

# Define targets
.PHONY: all build up down clean test

# Default target
all: build up

# Build the Docker image
build:
	$(DOCKER_COMPOSE) build

# Run the Docker container
up:
	$(DOCKER_COMPOSE) up -d

# Stop and remove the Docker container
down:
	$(DOCKER_COMPOSE) down

# Clean up Docker images and containers
clean:
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans

# Run tests
test:
	pytest

# Stop and remove the container, then run tests
test-run: down build up test down
