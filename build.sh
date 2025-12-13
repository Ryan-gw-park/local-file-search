#!/bin/bash
# Local Finder X v2.0 - Build Script
# Builds the application using PyInstaller

set -e

echo "==================================="
echo "Local Finder X v2.0 Build Script"
echo "==================================="

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Not in virtual environment"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build dist *.spec

# Create PyInstaller spec
echo ""
echo "Building application..."

pyinstaller \
    --name "LocalFinderX" \
    --windowed \
    --onefile \
    --icon "assets/icon.ico" \
    --add-data "assets:assets" \
    --hidden-import "PyQt6" \
    --hidden-import "sentence_transformers" \
    --hidden-import "lancedb" \
    --hidden-import "pyarrow" \
    --hidden-import "torch" \
    --collect-all "sentence_transformers" \
    --collect-all "transformers" \
    src/app/main.py

echo ""
echo "==================================="
echo "Build complete!"
echo "Output: dist/LocalFinderX"
echo "==================================="
