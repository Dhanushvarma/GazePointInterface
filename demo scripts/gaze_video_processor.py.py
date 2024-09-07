import cv2
import pandas as pd
import numpy as np
from datetime import datetime
import os
from typing import List, Tuple

def visualize_gaze_on_video_trailing(
    video_path: str,
    gaze_data_csv: str,
    output_video_path: str,
    trail_length: int = 5,
    use_pixels: bool = False
) -> None:
    df = pd.read_csv(gaze_data_csv)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Error opening video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    recent_gaze_points: List[Tuple[int, int]] = []

    for frame_count in range(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))):
        ret, frame = cap.read()
        if not ret:
            break

        recent_gaze_points = recent_gaze_points[-trail_length:]

        if frame_count in df['Frame'].values:
            gaze_points = df[df['Frame'] == frame_count]
            if use_pixels:
                new_points = gaze_points[['X_Pixel', 'Y_Pixel']].values
            else:
                new_points = gaze_points[['FPOGX', 'FPOGY']].values
                new_points[:, 0] *= width
                new_points[:, 1] *= height
            
            recent_gaze_points.extend(map(tuple, new_points.astype(int)))

        for i, (x, y) in enumerate(recent_gaze_points):
            opacity = int(255 * (i + 1) / len(recent_gaze_points))
            cv2.circle(frame, (x, y), 5, (0, 0, 255, opacity), -1)

        out.write(frame)

    cap.release()
    out.release()

def main():
    video_path = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\media\demo_8_video.mp4'
    gaze_data_csv = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\csv_gaze_data\gaze_data_video_20231120_143100.csv'
    output_visual_dir = r'C:\Users\Dhanush\PycharmProjects\gazepoint_LIRA\visuals'

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    visual_filename = f"gaze_data_video_{timestamp}.mp4"
    output_video_path = os.path.join(output_visual_dir, visual_filename)

    visualize_gaze_on_video_trailing(video_path, gaze_data_csv, output_video_path, use_pixels=True)

if __name__ == "__main__":
    main()