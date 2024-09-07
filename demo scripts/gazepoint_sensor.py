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

class GazeSensor:
    def __init__(self, output_dir):
        self.HOST = '127.0.0.1'
        self.PORT = 4242
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
        self.socket.connect((self.HOST, self.PORT))
        commands = [
            'ENABLE_SEND_CURSOR',
            'ENABLE_SEND_POG_FIX',
            'ENABLE_SEND_TIME',
            'ENABLE_SEND_DATA'
        ]
        for command in commands:
            self.socket.send(f'<SET ID="{command}" STATE="1" />\r\n'.encode())

    def get_secondary_display_position(self):
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
        num_displays = sdl2.SDL_GetNumVideoDisplays()
        if num_displays < 2:
            return 0, 0  # Default position for primary display
        display_bounds = sdl2.SDL_Rect()
        sdl2.SDL_GetDisplayBounds(1, display_bounds)
        return display_bounds.x, display_bounds.y

    def init_pygame_display(self, image_path):
        window_x, window_y = self.get_secondary_display_position()
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{window_x},{window_y}"

        pygame.init()
        displays = pygame.display.list_modes()
        target_display = displays[-1] if len(displays) > 1 else displays[0]
        self.screen = pygame.display.set_mode(target_display, pygame.FULLSCREEN)
        self.base_image = pygame.transform.scale(pygame.image.load(image_path), target_display)
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

    @staticmethod
    def gaussian_2d_kernel(kernel_size, sigma):
        x, y = np.ogrid[:kernel_size, :kernel_size]
        center = kernel_size // 2
        kernel = np.exp(-((x - center)**2 + (y - center)**2) / (2 * sigma**2))
        return kernel / kernel.max()

    def create_gaussian_blob(self, surface_size, sigma, max_opacity=255):
        kernel = self.gaussian_2d_kernel(surface_size, sigma)
        blob_rgb = np.zeros((surface_size, surface_size, 3), dtype=np.uint8)
        blob_rgb[..., 0] = 255  # Red channel
        alpha_channel = (kernel * max_opacity).astype(np.uint8)
        
        image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        pygame.surfarray.pixels_alpha(image)[:] = alpha_channel
        pygame.surfarray.pixels3d(image)[:] = blob_rgb
        
        return image

    def draw_marker_gaussian(self, x, y):
        self.screen.blit(self.base_image, (0, 0))
        self.screen.blit(self.marker_surface,
                         (x - self.marker_surface.get_width() // 2, y - self.marker_surface.get_height() // 2))
        pygame.display.flip()

    @staticmethod
    def normalized_to_pixel_values(x_from_gaze, y_from_gaze, display_size):
        return int(x_from_gaze * display_size[0]), int(y_from_gaze * display_size[1])

    def start_tracking(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"gaze_data_{self.media_name}_{timestamp}.csv"
        csv_path = os.path.join(self.output_dir, csv_filename)

        df = pd.DataFrame(columns=['Timestamp', 'FPOGX', 'FPOGY'])

        while pygame.time.get_ticks() < self.end_time:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

            data = self.socket.recv(1024).decode()
            parsed_data = self.parse_gaze_data(data)

            if parsed_data:
                x_pixel, y_pixel = self.normalized_to_pixel_values(parsed_data['FPOGX'], parsed_data['FPOGY'],
                                                                   self.screen.get_size())
                self.draw_marker_gaussian(x_pixel, y_pixel)
                df = df.append(parsed_data, ignore_index=True)

        df.to_csv(csv_path, index=False)
        pygame.quit()

    @staticmethod
    def parse_gaze_data(data):
        parsed_data = {}
        for item in data.split():
            if '=' in item:
                key, value = item.split('=')
                if key in ['FPOGX', 'FPOGY', 'TIME']:
                    try:
                        parsed_data[key] = float(value.strip('"'))
                    except ValueError:
                        continue
        return parsed_data if len(parsed_data) == 3 else None

    def play_video_and_track_gaze(self):
        df = pd.DataFrame(columns=['Frame', 'Timestamp', 'FPOGX', 'FPOGY', 'X_Pixel', 'Y_Pixel'])
        infoObject = pygame.display.Info()
        self.screen = pygame.display.set_mode((infoObject.current_w, infoObject.current_h), pygame.FULLSCREEN)

        frame_count = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame, k=-3)
            frame = np.flipud(frame)
            frame = pygame.surfarray.make_surface(frame)
            frame = pygame.transform.scale(frame, (infoObject.current_w, infoObject.current_h))

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.cap.release()
                    pygame.quit()
                    return df

            self.screen.blit(frame, (0, 0))
            pygame.display.flip()

            data = self.socket.recv(1024).decode()
            parsed_data = self.parse_gaze_data(data)

            if parsed_data:
                x_pixel, y_pixel = self.normalized_to_pixel_values(parsed_data['FPOGX'], parsed_data['FPOGY'],
                                                                   (infoObject.current_w, infoObject.current_h))
                parsed_data.update({'Frame': frame_count, 'X_Pixel': x_pixel, 'Y_Pixel': y_pixel})
                df = df.append(parsed_data, ignore_index=True)

            frame_count += 1
            self.clock.tick(self.fps)

        self.cap.release()
        pygame.quit()
        return df

def main():
    output_directory = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data'
    video_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\demo_8_video.mp4'

    gaze_sensor = GazeSensor(output_directory)
    gaze_sensor.connect_sensor()
    gaze_sensor.init_pygame_video_display(video_path)
    gaze_data = gaze_sensor.play_video_and_track_gaze()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"gaze_data_video_{timestamp}.csv"
    csv_path = os.path.join(output_directory, csv_filename)
    gaze_data.to_csv(csv_path, index=False)

if __name__ == "__main__":
    main()