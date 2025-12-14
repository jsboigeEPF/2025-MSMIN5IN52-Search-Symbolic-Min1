#!/bin/bash

# Job-Shop Scheduler - Quick Setup Script
# This script stops existing containers and starts the new React + FastAPI stack

set -e

echo "🏭 Job-Shop Scheduler Setup"
echo "============================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Remove old images (optional)
read -p "Remove old images to save space? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing old images..."
    docker image prune -a -f --filter "label=jobshop" 2>/dev/null || true
fi

echo ""
echo "🔨 Building and starting services..."
echo "This may take a few minutes on first run..."
echo ""

# Build and start services
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Wait for backend to be ready
echo "Checking backend health..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        echo "✓ Backend is ready"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  Backend took longer than expected to start"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📍 Access the application at:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 View logs with:  docker compose logs -f"
echo "🛑 Stop with:       docker compose down"
echo ""
echo "Opening frontend in browser..."

# Try to open browser (works on macOS, Linux with xdg-open, Windows with start)
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v start &> /dev/null; then
    start http://localhost:3000
fi

echo ""
echo "Happy scheduling! 🚀"
