import cv2
import pandas as pd
from PIL import Image, ImageDraw
import numpy as np
import os


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


# Example usage
image_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\example_image.jpeg'   # Replace with the path to your image
csv_path = r"C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data\gaze_data_example_image_20231117_175740.csv" # Replace with the path to your CSV file
output_video_path = 'output_video.mp4'  # Path for the output video

create_gaze_video(image_path, csv_path, output_video_path)
