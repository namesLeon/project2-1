from abc import ABC, abstractmethod
import vec2

class EyeTrackingInterface(ABC):
    @abstractmethod
    def getNormalizedGazePosition(self) -> vec2:
        """" Returns the normalized gaze position as a vec2 object. [0,1] range"""
        pass


    @abstractmethod
    def getSreenGazePosition(self) -> vec2:
        """ Returns the screen gaze position as a vec2 object. [0,screen_width] and [0,screen_height] range"""
        pass
    

    # Added method to check connection status, useful for error handling
    @abstractmethod
    def isConnected(self) -> bool:
        """ Returns True if the eye tracker is connected, False otherwise."""
        pass