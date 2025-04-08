#!/bin/bash
# Script to run the LLM Text Processor Docker container

# Create data directories if they don't exist
mkdir -p data/input data/output

# Check if input files were provided as arguments
if [ $# -gt 0 ]; then
  # Copy specified files to the input directory
  for file in "$@"; do
    if [ -f "$file" ]; then
      echo "Copying $file to data/input/"
      cp "$file" data/input/
    else
      echo "Warning: $file not found."
    fi
  done
fi

# Check if we have any files in the input directory
if [ -z "$(ls -A data/input/)" ]; then
  echo "No files in data/input/. Please add files before running."
  exit 1
fi

# Build and run the container
echo "Building and running the LLM Text Processor container..."
docker-compose up --build

# Print the results
echo "Processing complete! Check data/output/ for processed files."
