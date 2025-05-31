#!/bin/bash
echo "Starting FastAPI backend server..."
echo "Access the API at http://0.0.0.0:8000"
echo "Press Ctrl+C to stop the server."
uvicorn webapp.backend.main:app --reload --host 0.0.0.0 --port 8000
