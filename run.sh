#!/bin/bash
set -e  # Exit on error

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "     Starting GIFWA Launcher"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

spinner() {
    local pid=$!
    local delay=0.15
    local spin='🌕🌖🌗🌘🌑🌒🌓🌔'
    local i=0

    while kill -0 "$pid" 2>/dev/null; do
        printf "\r%s  Building..." "${spin:i:1}"
        i=$(( (i + 1) % ${#spin} ))
        sleep "$delay"
    done
    printf "\r✅ Build finished!            \n"
}

echo "🛠️  Building GIFWA project..."

rm -rf build
mkdir -p build

(
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --config Release
) &
spinner

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "    Launching Applications"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "▶️  Starting GIFWA..."

# You said you normally run: cd build && ./GIFWA
# So always launch GIFWA from inside the build directory.
if [[ -x "build/GIFWA" ]]; then
  echo "▶️  Starting GIFWA (cwd: build)..."
  (
      cd build
      ./GIFWA
  ) &
  GIFWA_PID=$!
elif [[ -x "build/Release/GIFWA" ]]; then
  # Fallback if your generator outputs into build/Release
  echo "▶️  Starting GIFWA (cwd: build/Release)..."
  (
      cd build/Release
      ./GIFWA
  ) &
  GIFWA_PID=$!
else
  echo "❌ Could not find GIFWA binary at build/GIFWA or build/Release/GIFWA"
  exit 1
fi

echo "👁️  Starting Eye Tracker..."
(
    python3 -m scripts.run_eye_tracker || python -m scripts.run_eye_tracker
) &
TRACKER_PID=$!

trap 'kill "$GIFWA_PID" "$TRACKER_PID" 2>/dev/null || true' EXIT

echo ""
echo "✨ Both services are running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

wait  # Keeps script alive
