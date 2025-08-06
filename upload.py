from pathlib import Path
from progresslib import ProgressController
from yt_utils import YoutubeUtils
from my_secrets import (
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    YOUTUBE_REFRESH_TOKEN,
    YOUTUBE_TOKEN,
    YOUTUBE_TOKEN_URI,
)

if __name__ == "__main__":
    PROGRESS_FILE = Path(__file__).parent / "progress.json"
    PROCESSED_DIR = Path(__file__).parent / "processed_videos"

    progress_controller = ProgressController(PROGRESS_FILE)
    process_log = progress_controller.load_progress()

    ytlib = YoutubeUtils(
        youtube_token=YOUTUBE_TOKEN,
        youtube_refresh_token=YOUTUBE_REFRESH_TOKEN,
        youtube_token_uri=YOUTUBE_TOKEN_URI,
        youtube_client_id=YOUTUBE_CLIENT_ID,
        youtube_client_secret=YOUTUBE_CLIENT_SECRET,
    )

    while True:
        next_item = progress_controller.read_and_move_next_item(
            "processed", "uploading"
        )
        if not next_item:
            print("No more items to upload.")
            exit(0)

        video_id, video_properties = next_item

        ytlib.upload(
            PROCESSED_DIR / video_properties.original_video_name,
            video_properties.new_video_name,
            description="",
            category_id="22",
            privacy="public",
        )

        ytlib.add_to_playlist(
            video_id,
            video_properties.new_playlist_id,
        )

        progress_controller.move_item("uploading", "uploaded", video_id)
