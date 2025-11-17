#!/bin/bash

echo "Waiting for services to be ready..."
sleep 10

echo "Running integration tests..."
pytest tests/ -v --tb=short

echo "Tests completed!"