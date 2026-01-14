#!/bin/bash
set -e  # Exit on error


echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "     Starting GIFWA Launcher 
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""


spinner() {
    local pid=$!
    local delay=0.15
    local spin='🌕🌖🌗🌘🌑🌒🌓🌔'

    while kill -0 "$pid" 2>/dev/null; do
        for i in $(seq 0 ${#spin}); do
            printf "\r%s" "${spin:i:1}  Building..."
            sleep $delay
        done
    done
    printf "\r✅ Build finished!            \n"
}


echo "🛠️  Building GIFWA project..."

rm -rf build
mkdir build

(
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --config Release
) &
spinner

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "    Launching Applications
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "▶️  Starting GIFWA..."
(
    cd build/Release
    ./GIFWA
) &
GIFWA_PID=$!


echo "👁️  Starting Eye Tracker..."
(
    python3 -m scripts.run_eye_tracker || python -m scripts.run_eye_tracker
) &
TRACKER_PID=$!

echo ""
echo "✨ Both services are running! 🤌🏽"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

wait   # Keeps script alive
