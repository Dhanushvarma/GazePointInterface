import socket
import pandas as pd
import os
import pygame
import time
import numpy as np
from datetime import datetime
import cv2
import sdl2
import sdl2.ext

"""
Script to capture gaze data on image for fixed duration and store in csv file
"""


class GazeSensor():
    def __init__(self, output_dir):
        self.HOST = '127.0.0.1'
        self.PORT = 4242
        self.ADDRESS = (self.HOST, self.PORT)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.screen = None
        self.base_image = None
        self.end_time = 0
        self.marker_surface = None
        self.duration = 10000  # In milliseconds
        self.output_dir = output_dir
        self.media_name = None


        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def connect_sensor(self):
        self.socket.connect(self.ADDRESS)
        # Send commands to initialize data streaming
        """
        Currently Hardcoded to get the following data from the server: Cursor location, POG (FPOGX, FPOGY), Timestamps
        """
        self.socket.send(str.encode('<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n'))
        self.socket.send(str.encode('<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'))
        self.socket.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
        self.socket.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))

    def get_secondary_display_position(self):
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
        num_displays = sdl2.SDL_GetNumVideoDisplays()
        if num_displays < 2:
            return 0, 0  # Default position for primary display

        display_index = 1  # Assuming the secondary monitor is what we want
        display_bounds = sdl2.SDL_Rect()
        sdl2.SDL_GetDisplayBounds(display_index, display_bounds)
        return display_bounds.x, display_bounds.y

    def init_pygame_display(self, image_path):
        window_x, window_y = self.get_secondary_display_position()
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{window_x},{window_y}"

        pygame.init()
        displays = pygame.display.list_modes()
        target_display = displays[0] if len(displays) == 1 else displays[-1]
        self.screen = pygame.display.set_mode(target_display, pygame.FULLSCREEN)
        self.base_image = pygame.image.load(image_path)
        self.base_image = pygame.transform.scale(self.base_image, target_display)
        self.screen.blit(self.base_image, (0, 0))
        pygame.display.flip()
        self.end_time = pygame.time.get_ticks() + self.duration
        self.marker_surface = self.create_gaussian_blob(50, 15, max_opacity=150)
        self.media_name = os.path.splitext(os.path.basename(image_path))[0]

    def init_pygame_video_display(self, video_path):
        window_x, window_y = self.get_secondary_display_position()
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{window_x},{window_y}"

        pygame.init()
        self.clock = pygame.time.Clock()
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise Exception("Error opening video file")

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)


    def gaussian_2d_kernel(self, kernel_size, sigma):
        """Generate 2D Gaussian kernel."""
        kernel = np.fromfunction(
            lambda x, y: (1 / (2 * np.pi * sigma ** 2)) *
                         np.exp(- ((x - (kernel_size - 1) / 2) ** 2 + (y - (kernel_size - 1) / 2) ** 2) / (
                                 2 * sigma ** 2)),
            (kernel_size, kernel_size)
        )
        return kernel / np.max(kernel)

    def create_gaussian_blob(self, surface_size, sigma, max_opacity=255):
        """Generate a Gaussian blob as a pygame Surface."""
        kernel = self.gaussian_2d_kernel(surface_size, sigma)

        # Create an RGB array from the Gaussian kernel
        blob_rgb = np.zeros((surface_size, surface_size, 3))
        blob_rgb[..., 0] = 255  # Red channel
        blob_rgb[..., 1] = 0  # Green channel
        blob_rgb[..., 2] = 0  # Blue channel
        blob_rgb = blob_rgb.astype(np.uint8)

        # Convert RGB array to a pygame surface
        image_rgb = pygame.surfarray.make_surface(blob_rgb)

        # Generate an alpha channel array from the Gaussian kernel
        alpha_channel = (kernel * max_opacity).astype(np.uint8)

        # Create an empty surface with SRCALPHA to handle transparency
        image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        # Set the RGBA values for each pixel of the surface
        for x in range(surface_size):
            for y in range(surface_size):
                r, g, b = blob_rgb[x, y]
                a = alpha_channel[x, y]
                image.set_at((x, y), (r, g, b, a))

        return image

    def draw_marker_gaussian(self, x, y):
        """
        :param x: The transformed gaze_x values to pixel position of the display along x axis
        :param y: The transformed gaze_y values to pixel position of the display along y axis
        :return: None
        """
        self.screen.blit(self.base_image, (0, 0))
        self.screen.blit(self.marker_surface,
                         (x - self.marker_surface.get_width() // 2, y - self.marker_surface.get_height() // 2))
        pygame.display.flip()

    @staticmethod
    def normalized_to_pixel_values(x_from_gaze, y_from_gaze, display_size):
        """
        :param x_from_gaze: Untransformed FPOGX (is between 0 and 1)
        :param y_from_gaze: Untransformed FPOGY (is between 0 and 1)
        :param display_size: contains the number of pixels along x and y axes
        :return: transformed (FPOGX, FPOGY) --> (pixel_x, pixel_y)
        """
        pixel_x = int(x_from_gaze * display_size[0])
        pixel_y = int(y_from_gaze * display_size[1])
        return pixel_x, pixel_y

    def start_tracking(self):

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"gaze_data_{self.media_name}_{timestamp}.csv"
        csv_path = os.path.join(self.output_dir, csv_filename)

        df = pd.DataFrame(columns=['Timestamp', 'FPOGX', 'FPOGY'])  # Initialize DataFrame to store gaze data

        while pygame.time.get_ticks() < self.end_time:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

            rxdat = self.socket.recv(1024)
            data = bytes.decode(rxdat)

            # Parse the data received from Gazepoint
            parsed_data = self.parse_gaze_data(data)

            if parsed_data:
                # Convert normalized gaze coordinates to pixel values
                x_pixel, y_pixel = self.normalized_to_pixel_values(parsed_data['FPOGX'], parsed_data['FPOGY'],
                                                                   self.screen.get_size())

                # Draw the gaze marker
                self.draw_marker_gaussian(x_pixel, y_pixel)

                # Append the data to the DataFrame
                df = df.append(parsed_data, ignore_index=True)

        df.to_csv(csv_path, index=False)
        pygame.quit()

    @staticmethod
    def parse_gaze_data(data):
        parsed_data = {}
        datalist = data.split(" ")

        for el in datalist:
            if "FPOGX=\"" in el:
                try:
                    parsed_data['FPOGX'] = float(el.split("\"")[1])
                except IndexError:
                    continue  # Skip if the expected format is not met

            if "FPOGY=\"" in el:
                try:
                    parsed_data['FPOGY'] = float(el.split("\"")[1])
                except IndexError:
                    continue

            if 'TIME="' in el:
                try:
                    time_value = el.split('"')[1]
                    parsed_data['TIME'] = float(time_value)
                except IndexError:
                    continue

        return parsed_data if 'FPOGX' in parsed_data and 'FPOGY' in parsed_data and 'TIME' in parsed_data else None


    def play_video_and_track_gaze(self):
        df = pd.DataFrame(columns=['Frame', 'Timestamp', 'FPOGX', 'FPOGY'])

        frame_count = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            # Convert frame to a format suitable for pygame
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = pygame.surfarray.make_surface(frame)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.cap.release()
                    pygame.quit()
                    return

            # Display the frame
            self.screen.blit(frame, (0, 0))
            pygame.display.flip()

            # Capture gaze data
            rxdat = self.socket.recv(1024)
            data = bytes.decode(rxdat)
            parsed_data = self.parse_gaze_data(data)

            if parsed_data:
                # Append gaze data with frame count
                parsed_data['Frame'] = frame_count
                df = df.append(parsed_data, ignore_index=True)

            frame_count += 1
            self.clock.tick(self.fps)  # Sync with video FPS

        self.cap.release()
        pygame.quit()
        return df


# Example usage for images
output_directory = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data'
image_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\example_image.jpeg'  # Replace with your image path

gaze_sensor = GazeSensor(output_directory)
gaze_sensor.connect_sensor()
gaze_sensor.init_pygame_display(image_path)
gaze_sensor.start_tracking()


#Example usage for Videos

# Example usage
# output_directory = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data'  # Replace with your desired output directory
# video_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\sample_video.mp4'  # Replace with your video path
#
# # Initialize the GazeSensor
# gaze_sensor = GazeSensor(output_directory)
#
# # Connect to the gaze sensor hardware
# gaze_sensor.connect_sensor()
#
# # Initialize the pygame display for video
# gaze_sensor.init_pygame_video_display(video_path)
#
# # Play the video and track gaze data
# gaze_data = gaze_sensor.play_video_and_track_gaze()
#
# # Save the gaze data to a CSV file
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# csv_filename = f"gaze_data_video_{timestamp}.csv"
# csv_path = os.path.join(output_directory, csv_filename)
# gaze_data.to_csv(csv_path, index=False)


