## Usage
- 1) Run eyetracker.py. A window titled "Tracking" showcasing your camera view should appear.
Note that MediaPipe FaceMesh is supported only up until Python 3.10. We recommend 3.10.11.
- 2) Run Virtual Room\Virtual Room.exe. A 1920x1080 window should pop up featuring the level.
Depending on your machine, you might have to install some (general) dependencies. The pop-up launch errors should be sufficient to understand how to fix any possible issues.

## Unity project & scripts
level1controller.cs is the script hooked to the main camera in the level. You can check the entire data processing pipeline and the implementation of off-axis projection in it.

By default, we do not share the project file as its about 2.7GB in size. 

## Footnotes
Even though it is tracked, z - relative depth is not used in rendering/camera modifications. This is due to very jittery data, especially under low light. Further testing reveals that both the tracking model, i.e. MediaPipe FaceMesh, and the poor quality of generic laptop webcams are at fault for the resulting unreliable data. Instead, we recommend a fixed viewing distance of about 50 cm for the best results.

## Troubleshooting 
- Make sure that the eye tracker is actually running. You should have visual confirmation of your camera view (title of the window is "Tracking"). 

- If after step 2 the scene is opened but everything seems frozen, check if port 5052 is not being used by another process already. In that case, terminate the process and the issue should go away.

