#!/bin/bash

# Start Emese Frontend
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start React app
echo "Starting Emese frontend..."
npm start

