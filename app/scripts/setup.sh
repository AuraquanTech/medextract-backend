#!/bin/bash
set -euo pipefail

echo "Setting up MedExtractAI backend..."

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please edit with your secrets"
fi

echo "Setup complete! Activate with: source .venv/bin/activate"
