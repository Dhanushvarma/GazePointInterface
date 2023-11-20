import cv2
import pandas as pd
import numpy as np
from datetime import datetime
import os


def visualize_gaze_on_video(video_path, gaze_data_csv, output_video_path):
    # Load gaze data from CSV
    df = pd.read_csv(gaze_data_csv)

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Error opening video file")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Prepare the video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Check if there is gaze data for this frame
        if frame_count in df['Frame'].values:
            # Get gaze data for this frame
            gaze_points = df[df['Frame'] == frame_count][['FPOGX', 'FPOGY']]

            # Draw gaze points on the frame
            for index, row in gaze_points.iterrows():
                x, y = int(row['FPOGX'] * width), int(row['FPOGY'] * height)
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)  # Red dot

        # Write the frame
        out.write(frame)

        frame_count += 1

    cap.release()
    out.release()


# Example usage
video_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\sample_video.mp4'  # Replace with the path to your video
gaze_data_csv = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data\gaze_data_video_20231119_193113.csv'  # Replace with the path to your CSV file
output_visual_dir =  r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\visuals'  # Path for the output video

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
visual_filename = f"gaze_data_video_{timestamp}.mp4"
output_video_path = os.path.join(output_visual_dir, visual_filename)

visualize_gaze_on_video(video_path, gaze_data_csv, output_video_path)
