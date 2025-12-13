#!/bin/bash
# Local Finder X v2.0 Initialization Script
# Run this script to set up the development environment.

set -e

echo "🚀 Local Finder X v2.0 - Environment Setup"
echo "==========================================="

# Check Python version
python3 --version

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run smoke test (check if app can start)
echo "✅ Running smoke test..."
python3 -c "from src.app import main; print('Import OK')"

echo ""
echo "🎉 Environment setup complete!"
echo "To start the app, run: python -m src.app.main"
