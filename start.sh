#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creazione ambiente virtuale..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

if [ -z "$1" ]; then
    echo "❌ Specifica il modulo da avviare (es. ./start.sh camera)"
    exit 1
fi

python3 main.py "$@"

