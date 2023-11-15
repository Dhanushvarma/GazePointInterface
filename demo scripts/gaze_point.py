import socket
import pandas as pd
import os
import pygame
import time
import numpy as np
from datetime import datetime

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

    def init_pygame_display(self, image_path):
        """
        :param image_path:
        :return: None
        Function to init the active display where the image will be shown,
        the actual image that will be shown and duration for how long the image
        will be shown and we also init the blob to visualize the marker to track
        gaze on image
        """
        pygame.init()
        displays = pygame.display.list_modes()
        target_display = displays[0] if len(displays) == 1 else displays[1]
        self.screen = pygame.display.set_mode(target_display, pygame.FULLSCREEN, display=0)
        self.base_image = pygame.image.load(image_path)
        self.base_image = pygame.transform.scale(self.base_image, target_display)
        self.screen.blit(self.base_image, (0, 0))
        pygame.display.flip()
        self.end_time = pygame.time.get_ticks() + self.duration  # 10 seconds in milliseconds
        self.marker_surface = self.create_gaussian_blob(50, 15, max_opacity=150)
        self.media_name = os.path.splitext(os.path.basename(image_path))[0]

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

        print(data)
        print(datalist)

        for el in datalist:
            if "FPOGX" in el:
                parsed_data['FPOGX'] = float(el.split("\"")[1])
            if "FPOGY" in el:
                parsed_data['FPOGY'] = float(el.split("\"")[1])
            if 'TIME="' in el:
                time_value = el.split('"')[1]
                parsed_data['TIME'] = float(time_value)
                # parsed_data['TIME'] = float(el.split("\"")[1])


        return parsed_data if 'FPOGX' in parsed_data and 'FPOGY' in parsed_data and 'TIME' in parsed_data else None


# Example usage
output_directory = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data'
image_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\example_image.jpeg'  # Replace with your image path

gaze_sensor = GazeSensor(output_directory)
gaze_sensor.connect_sensor()
gaze_sensor.init_pygame_display(image_path)
gaze_sensor.start_tracking()

