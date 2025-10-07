#!/bin/bash
echo "Installing SimDock 3.1..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found! Please install Python 3.8+ first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Install SimDock
echo "Installing SimDock..."
pip3 install -e .

echo "Installation complete!"
echo ""
echo "IMPORTANT: Make sure you have installed:"
echo "- UCSF ChimeraX"
echo "- AutoDock Vina"
echo "- Open Babel"
echo ""
echo "Run SimDock with: python3 main.py"