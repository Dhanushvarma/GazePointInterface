import socket
import pandas as pd
import os
import pygame
import time
import numpy as np

def initialize_display():
    pygame.init()
    displays = pygame.display.list_modes()
    target_display = displays[1] if len(displays) > 1 else displays[0]
    screen = pygame.display.set_mode(target_display, pygame.FULLSCREEN, display=1)
    return screen, target_display

def load_and_scale_image(image_path, target_display):
    image = pygame.image.load(image_path)
    return pygame.transform.scale(image, target_display)

def gaussian_2d_kernel(kernel_size, sigma):
    x, y = np.ogrid[:kernel_size, :kernel_size]
    center = kernel_size // 2
    kernel = np.exp(-((x - center)**2 + (y - center)**2) / (2 * sigma**2))
    return kernel / kernel.max()

def create_gaussian_blob(surface_size, sigma, max_opacity=255):
    kernel = gaussian_2d_kernel(surface_size, sigma)
    blob_rgb = np.zeros((surface_size, surface_size, 3), dtype=np.uint8)
    blob_rgb[..., 0] = 255  # Red channel
    alpha_channel = (kernel * max_opacity).astype(np.uint8)
    
    image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
    pygame.surfarray.pixels_alpha(image)[:] = alpha_channel
    pygame.surfarray.pixels3d(image)[:] = blob_rgb
    
    return image

def draw_marker_gaussian(screen, base_image, x, y, marker_surface):
    screen.blit(base_image, (0, 0))
    screen.blit(marker_surface, (x - marker_surface.get_width() // 2, y - marker_surface.get_height() // 2))
    pygame.display.flip()

def normalized_to_pixel_values(x_from_gaze, y_from_gaze, display_size):
    return int(x_from_gaze * display_size[0]), int(y_from_gaze * display_size[1])

def connect_to_gazepoint():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 4242))
    for command in ['ENABLE_SEND_CURSOR', 'ENABLE_SEND_POG_FIX', 'ENABLE_SEND_DATA']:
        s.send(f'<SET ID="{command}" STATE="1" />\r\n'.encode())
    return s

def parse_gazepoint_data(data):
    datalist = data.split()
    return {key: float(value.strip('"')) for item in datalist for key, value in [item.split('=')]}

def main():
    screen, target_display = initialize_display()
    image = load_and_scale_image(r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\demo scripts\example_image.jpeg', target_display)
    marker_surface = create_gaussian_blob(50, 15, max_opacity=150)
    
    s = connect_to_gazepoint()
    
    end_time = pygame.time.get_ticks() + 10000  # 10 seconds
    
    while pygame.time.get_ticks() < end_time:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                return

        data = parse_gazepoint_data(s.recv(1024).decode())
        time.sleep(0.03)  # 30 ms sleep

        x_draw, y_draw = normalized_to_pixel_values(data.get('FPOGX', 0), data.get('FPOGY', 0), target_display)
        draw_marker_gaussian(screen, image, x_draw, y_draw, marker_surface)

        new_data = pd.DataFrame([data])
        if os.path.exists('gaze_data_output.csv'):
            df = pd.read_csv('gaze_data_output.csv')
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df = new_data
        df.to_csv('gaze_data_output.csv', index=False)

    pygame.quit()

if __name__ == "__main__":
    main()