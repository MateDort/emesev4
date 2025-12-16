#!/usr/bin/env python3
"""
Root-level entry point for Railway deployment.
This file allows Railway to detect Python and then runs the backend.
"""
import os
import sys

# Add backend to path and change directory
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# Import and run the FastAPI app from backend
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

