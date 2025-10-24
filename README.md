# Team_08 Project 2-1: Venice parallex effect

## How to build
- Firstly we want to make sure were in the "team_08" directory
- We need to make sure the "team_08/build" directory is deleted
- Run the following commands
  ```bash
  rm -rf build
  mkdir build
  cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  cmake --build build --config Release
  ```

## What you should be seeing
You should now be on a boat in venice, the eye tracker is working, so if you move your head around you should be seeing the parallex effect.

<!-- - Our script for running the our code is located in: "team_08/scripts/run_eye_tracker.py".  -->
