######################################################################################
# GazepointAPI.py - Example Client
# Written in 2013 by Gazepoint www.gazept.com
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this
# software. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
######################################################################################

import socket
import pandas as pd
import os
import pygame
import time
import numpy as np


# Initialize pygame
pygame.init()

# Identify available displays
displays = pygame.display.list_modes()

# For this example, we will display on the second monitor (if it exists)
# If not, it'll default to the primary monitor
if len(displays) > 1:
    target_display = displays[1]
else:
    target_display = displays[0]

print(target_display[0])

# Set up the display in fullscreen mode on the chosen screen
screen = pygame.display.set_mode(target_display, pygame.FULLSCREEN, display=1)

# Load the image (replace 'your_image.png' with your image's path)
image_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\demo scripts\example_image.jpeg'
image = pygame.image.load(image_path)
image = pygame.transform.scale(image, target_display)

# Display the image
screen.blit(image, (0, 0))
pygame.display.flip()

# Display the image
screen.blit(image, (0, 0))
pygame.display.flip()

# Set the duration (e.g., 10 seconds)
duration_ms = 10000  # 10 seconds in milliseconds
end_time = pygame.time.get_ticks() + duration_ms


###
def gaussian_2d_kernel(kernel_size, sigma):
    """Generate 2D Gaussian kernel."""
    kernel = np.fromfunction(
        lambda x, y: (1/ (2 * np.pi * sigma**2)) *
                     np.exp(- ((x - (kernel_size - 1) / 2) ** 2 + (y - (kernel_size - 1) / 2) ** 2) / (2 * sigma**2)),
        (kernel_size, kernel_size)
    )
    return kernel / np.max(kernel)


def create_gaussian_blob(surface_size, sigma, max_opacity=255):
    """Generate a Gaussian blob as a pygame Surface."""
    kernel = gaussian_2d_kernel(surface_size, sigma)

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



def draw_marker_gaussian(screen, base_image, x, y, marker_surface):
    """Draw the base image and a marker at (x, y) on the given screen."""
    screen.blit(base_image, (0, 0))
    screen.blit(marker_surface, (x - marker_surface.get_width() // 2, y - marker_surface.get_height() // 2))
    pygame.display.flip()


marker_surface = create_gaussian_blob(50, 15, max_opacity=150) # Change Params



def draw_marker(screen, base_image, x, y):
    """Draw the base image and a marker at (x, y) on the given screen."""
    # Draw the base image first
    screen.blit(base_image, (0, 0))

    # Draw the marker
    pygame.draw.circle(screen, (255, 0, 0), (x, y), 10)  # 10 is the radius of the dot

    # Refresh the display
    pygame.display.flip()


def normalized_to_pixel_values(x_from_gaze, y_from_gaze):
    pixel_x = int(x_from_gaze * target_display[0])
    pixel_y = int(y_from_gaze * target_display[1])
    return pixel_x, pixel_y

###
# Host machine IP
HOST = '127.0.0.1'
# Gazepoint Port
PORT = 4242
ADDRESS = (HOST, PORT)

# Connect to Gazepoint API
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(ADDRESS)

# Send commands to initialize data streaming
s.send(str.encode('<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n'))
s.send(str.encode('<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'))
s.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))

while pygame.time.get_ticks() < end_time:
    for event in pygame.event.get():
        # Close the fullscreen display if the 'esc' key is pressed
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            break

    rxdat = s.recv(1024)
    data = bytes.decode(rxdat)
    print(data)
    time.sleep(30 / 1000)

    # Parse data string
    FPOGX = 0
    FPOGY = 0
    FPOGV = 0
    CX = 0
    CY = 0

    # Split data string into a list of name="value" substrings
    datalist = data.split(" ")

    # Iterate through list of substrings to extract data values
    for el in datalist:
        if el.find("FPOGX") != -1:
            FPOGX = float(el.split("\"")[1])

        if el.find("FPOGY") != -1:
            FPOGY = float(el.split("\"")[1])

        # if (el.find("FPOGV") != -1):
        #     FPOGV = float(el.split("\"")[1])
        #
        # if (el.find("CX") != -1):
        #     CX = float(el.split("\"")[1])
        #
        # if (el.find("CY") != -1):
        #     CY = float(el.split("\"")[1])

        data = {
            'FPOGX': FPOGX,
            'FPOGY': FPOGY
            # 'FPOGV': FPOGV,
            # 'CX': CX,
            # 'CY': CY
        }

    x_draw, y_draw = normalized_to_pixel_values(FPOGX, FPOGY)

    # draw_marker(screen, image, x_draw, y_draw)
    draw_marker_gaussian(screen, image, x_draw, y_draw, marker_surface)
    # Convert dictionary to a DataFrame

    new_data = pd.DataFrame([data])

    # Check if CSV exists to append or create new
    if os.path.exists('output.csv'):
        # Read existing data
        try:
            df = pd.read_csv('output.csv')
        except:
            df = pd.DataFrame()

        # Append new data
        df = df.append(new_data, ignore_index=True)
    else:
        df = new_data

    # Write the DataFrame back to CSV
    df.to_csv('output.csv', index=False)

pygame.quit()
