"""
Utility class for processing eye-tracking gaze data and converting coordinates
to pixel positions on a screen.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import re
import numpy as np
from numpy.typing import NDArray


@dataclass
class GazeCoordinates:
    """Data class to store processed gaze coordinates."""
    pixel_x: float
    pixel_y: float


class GazeDataUtil:
    """
    A utility class for processing eye-tracking gaze data and converting
    normalized coordinates to pixel positions on a screen.
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """
        Initialize the GazeDataUtil with screen dimensions.

        Args:
            screen_width: Width of the screen in pixels
            screen_height: Height of the screen in pixels

        Raises:
            ValueError: If screen dimensions are not positive integers
        """
        if not isinstance(screen_width, int) or not isinstance(screen_height, int):
            raise ValueError("Screen dimensions must be integers")
        if screen_width <= 0 or screen_height <= 0:
            raise ValueError("Screen dimensions must be positive")

        self.screen_height = screen_height
        self.screen_width = screen_width

    @staticmethod
    def extract_data(input_string: str) -> Dict[str, float]:
        """
        Extract gaze data parameters from a formatted input string.

        Args:
            input_string: String containing gaze data in format 'KEY="VALUE"'

        Returns:
            Dictionary containing parsed gaze parameters

        Raises:
            ValueError: If input string is empty or malformed
        """
        if not input_string or not isinstance(input_string, str):
            raise ValueError("Input must be a non-empty string")

        pattern = r'(\w+)="([-+]?\d*\.?\d+)"'
        matches = re.findall(pattern, input_string)

        if not matches:
            raise ValueError("No valid gaze data found in input string")

        return {key: float(value) for key, value in matches}

    def validate_gaze_coordinates(self, x: float, y: float) -> None:
        """
        Validate that gaze coordinates are within the expected range [0, 1].

        Args:
            x: Normalized x coordinate
            y: Normalized y coordinate

        Raises:
            ValueError: If coordinates are outside the valid range
        """
        if not (0 <= x <= 1 and 0 <= y <= 1):
            raise ValueError(
                f"Gaze coordinates must be between 0 and 1. Got x={x}, y={y}"
            )

    def gaze_to_pixels(self, gaze_input: str) -> Tuple[GazeCoordinates, Dict[str, float]]:
        """
        Convert normalized gaze coordinates to pixel coordinates.

        Args:
            gaze_input: String containing gaze data parameters

        Returns:
            Tuple containing:
                - GazeCoordinates object with pixel coordinates
                - Dictionary of all extracted gaze parameters

        Raises:
            ValueError: If required gaze parameters are missing or invalid
        """
        gaze_data = self.extract_data(gaze_input)

        try:
            x = gaze_data['FPOGX']
            y = gaze_data['FPOGY']
        except KeyError as e:
            raise ValueError(f"Missing required gaze parameter: {e}")

        self.validate_gaze_coordinates(x, y)

        pixel_coords = GazeCoordinates(
            pixel_x=self.screen_width * x,
            pixel_y=self.screen_height * y
        )

        return pixel_coords, gaze_data

    def transform_coordinate_system(
        self,
        coordinates: NDArray[np.float64],
        origin: str = 'top_left'
    ) -> NDArray[np.float64]:
        """
        Transform coordinates between different coordinate system origins.
        Currently supports 'top_left' (default) and 'bottom_left' origins.

        Args:
            coordinates: Nx2 array of (x, y) coordinates
            origin: Desired coordinate system origin ('top_left' or 'bottom_left')

        Returns:
            Transformed coordinates in the specified coordinate system

        Raises:
            ValueError: If origin is not supported or coordinates array is invalid
        """
        if origin not in ['top_left', 'bottom_left']:
            raise ValueError("Supported origins are 'top_left' and 'bottom_left'")

        if not isinstance(coordinates, np.ndarray) or coordinates.shape[1] != 2:
            raise ValueError("Coordinates must be an Nx2 numpy array")

        if origin == 'bottom_left':
            coordinates[:, 1] = self.screen_height - coordinates[:, 1]

        return coordinates