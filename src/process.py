from pathlib import Path
from src.progresslib import ProgressController, ProgressState
from src.video_processor import VideoProcessor


if __name__ == "__main__":
    PROGRESS_FILE = Path("progress.json")
    DOWNLOAD_DIR = Path("downloaded_videos")
    PROCESSING_DIR = Path("processing_videos")
    PROCESSED_DIR = Path("processed_videos")

    progress_controller = ProgressController(PROGRESS_FILE)

    while True:
        # Acquire lock to safely read and update progress file
        next_item = progress_controller.read_and_move_next_item(
            ProgressState.DOWNLOADED, ProgressState.PROCESSING
        )

        if not next_item:
            print("No more items to process.")
            exit(0)

        video_id, video_properties = next_item

        # Process the video
        try:
            VideoProcessor.process(
                DOWNLOAD_DIR / f"{video_properties.original_video_name}.mp4",
                PROCESSED_DIR / f"{video_properties.new_video_name}.mp4",
            )
        except Exception as e:
            print(f"Error processing video {video_id}: {e}")
            progress_controller.move_item(
                ProgressState.PROCESSING, ProgressState.DOWNLOADED, video_id
            )
            continue

        progress_controller.move_item(
            ProgressState.PROCESSING, ProgressState.PROCESSED, video_id
        )
