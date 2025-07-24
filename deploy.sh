#!/bin/bash

# WhatsApp Chat Viewer - Production Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
PROJECT_NAME="whatsapp-chat-viewer"

echo "🚀 Starting deployment for $ENVIRONMENT environment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy .env.example to .env and configure it."
    echo "cp .env.example .env"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
required_vars=("SECRET_KEY" "DATABASE_URL" "POSTGRES_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set in .env file"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Pull latest images and rebuild
echo "🔄 Building application..."
docker-compose build --no-cache

# Start services
echo "🐳 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 15

# Check if services are healthy
echo "🔍 Checking service health..."
if docker-compose ps | grep -q "unhealthy\|Exit"; then
    echo "❌ Some services are not healthy:"
    docker-compose ps
    echo "📋 Checking logs..."
    docker-compose logs --tail=50
    exit 1
fi

echo "✅ Deployment completed successfully!"
echo "🌐 Application is running on port ${APP_PORT:-5000}"
echo "📊 Check status: docker-compose ps"
echo "📋 View logs: docker-compose logs -f"