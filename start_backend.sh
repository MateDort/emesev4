#!/bin/bash

# Start Emese Backend Server
cd "$(dirname "$0")/backend" || exit 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Check if we're in venv (safety check)
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment not activated. Activating now..."
    source venv/bin/activate
fi

# Initialize database
echo "Initializing database..."
python3 -c "from database.database import init_db; init_db()" || echo "Database initialization skipped (may already exist)"

# Start server
echo "Starting Emese backend server..."
echo "Server will be available at http://localhost:8000"
echo "API docs at http://localhost:8000/docs"
python3 main.py

