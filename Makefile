# Define variables
DOCKER_COMPOSE = docker-compose
DOCKER_IMAGE_NAME = test-postgres

# Define targets
.PHONY: all build up down clean test prune test-run

# Default target
all: build up

# Build the Docker images
build:
	$(DOCKER_COMPOSE) build

# Run the Docker containers
up:
	$(DOCKER_COMPOSE) up -d

# Stop and remove the Docker containers
down:
	$(DOCKER_COMPOSE) down

# Clean up Docker images, containers, and volumes
clean:
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans

# Prune Docker system to remove unused data
prune:
	docker system prune -f
	docker container prune -f
	docker volume prune -f
	docker network prune -f

# Run tests
test:
	pytest

# Stop and remove the containers, then run tests
test-run: prune build up test down
