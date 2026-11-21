#!/bin/bash
# AI Farmer - Production Setup Script
set -e

echo "🌾 AI Farmer - Production Setup"
echo "==============================="

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "⬆️  Upgrading pip..."
pip install --upgrade pip

echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "📁 Creating directories..."
mkdir -p data/uploads data/models logs

echo "⚙️  Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file. Please edit it with your API keys."
else
    echo "✓ .env file already exists"
fi

echo "🗄️  Initializing database..."
python3 -c "from app.services.database import db_service; print('Database initialized successfully')"

echo "🧪 Running tests..."
python3 -m pytest tests/ -v || echo "⚠️  Some tests failed. Check test output."

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Run: python main.py"
echo "3. Open: http://localhost:8000"
echo "4. API Docs: http://localhost:8000/docs"
echo ""
echo "🌾 Happy Farming with AI!"
