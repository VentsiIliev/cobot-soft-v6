#!/bin/bash

VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists."
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found"
fi

echo ""
echo "Setup complete!"
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"

