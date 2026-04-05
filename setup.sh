#!/bin/bash
echo "Setting up BTC Trading Project..."
echo "================================="

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

mkdir -p data/raw data/processed
mkdir -p logs results

echo "Setup complete!"
echo "To activate: source venv/bin/activate"
