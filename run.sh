#!/bin/bash
set -e  # Exit on error

# Build and run Venice Parallax Effect project
echo "Building GIFWA..."
rm -rf build
mkdir build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

echo "Starting GIFWA and eye tracker..."

# Start GIFWA in background with correct working directory
(cd build/Release && ./GIFWA) &
GIFWA_PID=$!

# Start eye tracker in background
(python3 -m scripts.run_eye_tracker || python -m scripts.run_eye_tracker) &
TRACKER_PID=$!

echo "Both running."
wait