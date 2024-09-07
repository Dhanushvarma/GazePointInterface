import cv2
import pandas as pd
from PIL import Image, ImageDraw
import numpy as np
import os
from datetime import datetime
from typing import Tuple, List

def create_gaze_video(image_path: str, csv_path: str, output_video_path: str, frame_rate: int = 30):
    df = pd.read_csv(csv_path)
    image = Image.open(image_path)
    image_width, image_height = image.size

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, frame_rate, (image_width, image_height))

    for _, row in df.iterrows():
        frame = image.copy()
        draw = ImageDraw.Draw(frame)

        x, y = row['FPOGX'] * image_width, row['FPOGY'] * image_height
        radius = 5
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill='red', outline='red')

        opencv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        video.write(opencv_frame)

    video.release()

def create_gaze_video_trailing(image_path: str, csv_path: str, output_video_path: str, frame_rate: int = 30, trail_length: int = 10):
    df = pd.read_csv(csv_path)
    image = Image.open(image_path)
    image_width, image_height = image.size

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, frame_rate, (image_width, image_height))

    recent_gaze_points: List[Tuple[float, float]] = []

    for _, row in df.iterrows():
        frame = image.copy()
        draw = ImageDraw.Draw(frame)

        recent_gaze_points.append((row['FPOGX'] * image_width, row['FPOGY'] * image_height))
        recent_gaze_points = recent_gaze_points[-trail_length:]

        for i, (x, y) in enumerate(recent_gaze_points):
            opacity = int(255 * (i + 1) / len(recent_gaze_points))
            radius = 5
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), 
                         fill=(255, 0, 0, opacity), outline=(255, 0, 0, opacity))

        opencv_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGBA2BGRA)
        video.write(opencv_frame)

    video.release()

def main():
    image_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\example_image.jpeg'
    csv_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data\gaze_data_example_image_20231119_193509.csv'
    output_visual_dir = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\visuals'

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    visual_filename = f"gaze_data_video_{timestamp}.mp4"
    output_video_path = os.path.join(output_visual_dir, visual_filename)

    create_gaze_video_trailing(image_path, csv_path, output_video_path)

if __name__ == "__main__":
    main()