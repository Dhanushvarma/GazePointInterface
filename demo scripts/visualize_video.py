import cv2
import pandas as pd
import numpy as np
from datetime import datetime
import os


def visualize_gaze_on_video_trailing(video_path, gaze_data_csv, output_video_path, trail_length=5, use_pixels=False):
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

    # Initialize a list to store recent gaze points
    recent_gaze_points = []

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Keep only the last 'trail_length' gaze points
        recent_gaze_points = recent_gaze_points[-trail_length:]

        # Check if there is gaze data for this frame and add it to recent_gaze_points
        if frame_count in df['Frame'].values:
            if use_pixels:
                gaze_points = df[df['Frame'] == frame_count][['X_Pixel', 'Y_Pixel']]
            else:
                gaze_points = df[df['Frame'] == frame_count][['FPOGX', 'FPOGY']]
                gaze_points['FPOGX'] *= width
                gaze_points['FPOGY'] *= height

            for index, row in gaze_points.iterrows():
                recent_gaze_points.append((int(row.iloc[0]), int(row.iloc[1])))

        # Draw the gaze points with fading effect
        for i, (x, y) in enumerate(recent_gaze_points):
            opacity = int(255 * (i + 1) / len(recent_gaze_points))  # Increase opacity for recent points
            cv2.circle(frame, (x, y), 5, (0, 0, 255, opacity), -1)

        # Write the frame
        out.write(frame)

        frame_count += 1

    cap.release()
    out.release()

# Example usage
video_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\demo_8_video.mp4'  # Replace with the path to your video
gaze_data_csv = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data\gaze_data_video_20231120_143100.csv'  # Replace with the path to your CSV file
output_visual_dir =  r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\visuals'  # Path for the output video

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
visual_filename = f"gaze_data_video_{timestamp}.mp4"
output_video_path = os.path.join(output_visual_dir, visual_filename)

visualize_gaze_on_video_trailing(video_path, gaze_data_csv, output_video_path, use_pixels=True)
