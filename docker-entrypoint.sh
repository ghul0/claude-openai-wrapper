#!/bin/bash

# Start the application directly
exec python -m uvicorn app:app --host 0.0.0.0 --port 8000