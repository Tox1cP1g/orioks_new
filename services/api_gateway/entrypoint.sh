#!/bin/bash
set -e

echo "Starting API Gateway..."
exec uvicorn main:app --host 0.0.0.0 --port 8080 --reload 