# Team_08 Project 2-1: Venice parallex effect

<<<<<<< HEAD
## How to run shader and eye tracker using bash script
 - To run the bash script, the Git Bash terminal
 - Make sure you are inside the team_08 directory
 - Run the following command:
 - ./run.sh
 - If the command does not execute, run the following command:
 - chmod +x run.sh

## How to build shader
- Firstly we want to make sure were in the "team_08" directory
- We need to make sure the "team_08/build" directory is deleted
- Run the following commands
  ```bash(Optional if windows/Linux)
  rm -rf build
  mkdir build
  cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  cmake --build build --config Release
  ```
  (it should be in the Release)
  Mandatory
  ```bash
  cd build/Release
  run ./GIFWA
  ```

## How to run eye tracker
- in a new terminal you want to make sure you are in the `team_08` directory then run the line: `python3 -m scripts.run_eye_tracker`
- click 'esc' or 'q' to kill

## What you should be seeing
You should now be on a boat in venice, the eye tracker is not fully working (yet), we are writing to the gaze_out.txt file and the position should update.

=======
## How to build shader
- Firstly we want to make sure were in the "team_08" directory
- We need to make sure the "team_08/build" directory is deleted
- Run the following commands
  ```bash(Optional if windows/Linux)
  rm -rf build
  mkdir build
  cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  cmake --build build --config Release
  ```
  (it should be in the Release)
  Mandatory
  ```bash
  cd build/Release
  run ./GIFWA
  ```

## How to run eye tracker
- in a new terminal you want to make sure you are in the `team_08` directory then run the line: `python3 -m scripts.run_eye_tracker`
- click 'esc' or 'q' to kill

## What you should be seeing
You should now be on a boat in venice, the eye tracker is not fully working (yet), we are writing to the gaze_out.txt file and the position should update.

>>>>>>> c7a5110e96cd28a5524743bebd3e87fc40a6bf4c
<!-- - Our script for running the our code is located in: "team_08/scripts/run_eye_tracker.py".  -->
