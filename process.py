import json
from filelock import FileLock
from pathlib import Path

import yaml

from progresslib import ProgressController
from video_processor import VideoProcessor


if __name__ == "__main__":
    PROGRESS_FILE = Path(__file__).parent / "progress.json"
    DOWNLOAD_DIR = Path(__file__).parent / "downloaded_videos"
    PROCESSING_DIR = Path(__file__).parent / "processing_videos"
    PROCESSED_DIR = Path(__file__).parent / "processed_videos"

    progress_controller = ProgressController(PROGRESS_FILE)

    while True:
        # Acquire lock to safely read and update progress file
        next_item = progress_controller.read_and_move_next_item(
            "downloaded", "processing"
        )

        if not next_item:
            print("No more items to process.")
            exit(0)

        video_id, video_properties = next_item

        # Process the video
        VideoProcessor.process(
            DOWNLOAD_DIR / video_properties.original_video_id,
            PROCESSED_DIR / video_properties.new_video_name,
        )

        progress_controller.move_item("processing", "processed", video_id)
