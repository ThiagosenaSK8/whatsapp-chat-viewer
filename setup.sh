#!/bin/bash

# WhatsApp Chat Viewer - Initial Setup Script
# Usage: ./setup.sh

set -e

echo "🚀 WhatsApp Chat Viewer - Initial Setup"
echo "======================================="

# Check if running on Windows (Git Bash/WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "⚠️  Detected Windows environment. Make sure Docker Desktop is running."
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is installed and running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    echo "Please install docker-compose"
    exit 1
fi

echo "✅ docker-compose is available"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env file with your production values before deployment!"
    echo "   - Change SECRET_KEY to a secure random string"
    echo "   - Set a strong POSTGRES_PASSWORD"
    echo "   - Configure DATABASE_URL if using external database"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads/thumbnails
mkdir -p backups

# Set permissions (Linux/macOS only)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    chmod +x deploy.sh
    chmod +x backup.sh
    echo "✅ Scripts made executable"
fi

# Generate a random secret key if needed
if grep -q "your-super-secret-key-here-change-this" .env 2>/dev/null; then
    echo "🔑 Generating random SECRET_KEY..."
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i.bak "s/your-super-secret-key-here-change-this/$SECRET_KEY/" .env
        rm -f .env.bak
        echo "✅ SECRET_KEY generated and updated in .env"
    else
        echo "⚠️  Please manually update SECRET_KEY in .env file"
    fi
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review and edit .env file with your configuration"
echo "2. Run: ./deploy.sh production"
echo "3. Access your application at http://localhost:5000"
echo ""
echo "Default login credentials:"
echo "📧 Email: admin@admin.com"
echo "🔑 Password: admin123"
echo ""
echo "For monitoring: ./backup.sh monitor"
echo "For backups: ./backup.sh backup"