#!/bin/bash

if [ ! -d "./.venv" ]; then
  echo "Creating virtual environment.."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing requirements.."
python3 -m pip install -r requirements.txt
