#!/usr/bin/env bash
set -e

echo "🔍 Checking required tools..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not installed."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "❌ Docker Compose not available."; exit 1; }
command -v node >/dev/null 2>&1 || echo "⚠️  Node.js not found (needed only for frontend local dev, not required for Docker)."

echo "✅ Tools OK."

echo "🔧 Setting up .env..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Created .env from .env.example"
else
  echo "ℹ️  .env already exists, skipping."
fi

echo "🚀 Starting all services..."
docker compose up -d --build

echo "⏳ Waiting for services to be healthy..."
sleep 15
docker compose ps

echo "🌱 Seeding demo data..."
docker compose exec fastapi python scripts/seed.py || python scripts/seed.py

echo "✅ Setup complete!"
echo "   Frontend: http://localhost:3000"
echo "   API:      http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"