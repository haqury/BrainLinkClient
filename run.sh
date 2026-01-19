#!/bin/bash
# BrainLink Client Launcher for Linux/macOS

echo "Starting BrainLink Client..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "And: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
python -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Dependencies not installed!"
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run application
python main.py

# Deactivate virtual environment
deactivate

echo ""
echo "Application closed."
