#!/bin/bash
# scripts/docker-entrypoint.sh
# Docker entrypoint script for the backend service

set -e

echo "Starting Intelligent DSS Backend..."

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready (optional)
# echo "Waiting for Redis..."
# while ! nc -z redis 6379; do
#   sleep 1
# done
# echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"

# Make the entrypoint script executable
chmod +x scripts/docker-entrypoint.sh