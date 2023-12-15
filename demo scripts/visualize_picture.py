import cv2
import pandas as pd
from PIL import Image, ImageDraw
import numpy as np
import os
from datetime import datetime


def create_gaze_video(image_path, csv_path, output_video_path, frame_rate=30):
    # Load the gaze data
    df = pd.read_csv(csv_path)

    # Load the image
    image = Image.open(image_path)
    image_width, image_height = image.size

    # Prepare the video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, frame_rate, (image_width, image_height))

    # Iterate through the gaze data and create each frame
    for index, row in df.iterrows():
        frame = image.copy()
        draw = ImageDraw.Draw(frame)

        # Draw the gaze point
        x, y = row['FPOGX'] * image_width, row['FPOGY'] * image_height
        radius = 5  # Radius of the gaze point
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill='red', outline='red')

        # Convert PIL Image to OpenCV format and write frame
        opencv_frame = np.array(frame)
        opencv_frame = cv2.cvtColor(opencv_frame, cv2.COLOR_RGB2BGR)
        video.write(opencv_frame)

    video.release()


def create_gaze_video_trailing(image_path, csv_path, output_video_path, frame_rate=30, trail_length=10):
    # Load the gaze data
    df = pd.read_csv(csv_path)

    # Load the image
    image = Image.open(image_path)
    image_width, image_height = image.size

    # Prepare the video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video_path, fourcc, frame_rate, (image_width, image_height))

    # Initialize a list to store recent gaze points
    recent_gaze_points = []

    # Iterate through the gaze data and create each frame
    for index, row in df.iterrows():
        frame = image.copy()
        draw = ImageDraw.Draw(frame)

        # Update recent gaze points list
        recent_gaze_points.append((row['FPOGX'] * image_width, row['FPOGY'] * image_height))
        recent_gaze_points = recent_gaze_points[-trail_length:]

        # Draw the gaze points with fading effect
        for i, (x, y) in enumerate(recent_gaze_points):
            opacity = int(255 * (i + 1) / len(recent_gaze_points))  # Increase opacity for recent points
            radius = 5  # You can also vary radius based on 'i' for additional effect
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 0, 0, opacity), outline=(255, 0, 0, opacity))

        # Convert PIL Image to OpenCV format and write frame
        opencv_frame = np.array(frame)
        opencv_frame = cv2.cvtColor(opencv_frame, cv2.COLOR_RGBA2BGRA)
        video.write(opencv_frame)

    video.release()

# Example usage
image_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\example_image.jpeg'   # Replace with the path to your image
csv_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data\gaze_data_example_image_20231119_193509.csv' # Replace with the path to your CSV file
output_visual_dir = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\visuals'  # Path for the output video

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
visual_filename = f"gaze_data_video_{timestamp}.mp4"
output_video_path = os.path.join(output_visual_dir, visual_filename)

create_gaze_video_trailing(image_path, csv_path, output_video_path)
