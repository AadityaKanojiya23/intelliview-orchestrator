# Docker Deployment

## Docker build steps
Run `docker build -t app .` from the project root.

## Docker Compose commands
`docker compose up -d` to start services.
`docker compose ps` to check running containers.
`docker compose logs` to check logs.

## Required environment variables
See `.env.example` for the full list.

## How deployment works after merging to main
Merging to main triggers the CI/CD pipeline which builds and pushes the image.

## Docker Hub image information
Images are published to the project's Docker Hub repository on merge.
