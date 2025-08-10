from pathlib import Path
from progresslib import ProgressController, ProgressState
from yt_utils import YoutubeUtils
from my_secrets import (
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    YOUTUBE_REFRESH_TOKEN,
    YOUTUBE_TOKEN,
    YOUTUBE_TOKEN_URI,
    CHANNEL_ID,
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
        channel_id=CHANNEL_ID,
    )

    failed_ids = []
    while True:
        next_item = progress_controller.read_and_move_next_item(
            ProgressState.PROCESSED, ProgressState.UPLOADING
        )
        if not next_item:
            print("No more items to upload.")
            break

        video_id, video_properties = next_item

        try:
            new_video = ytlib.upload(
                PROCESSED_DIR / f"{video_properties.new_video_name}.mp4",
                video_properties.new_video_name,
                description="",
                category_id="22",
                privacy="public",
            )

            ytlib.add_to_playlist(
                new_video.id,
                video_properties.new_playlist_id,
            )
        except Exception as e:
            print(f"Error uploading video {video_id}: {e}")
            failed_ids.append(video_id)
            continue

        progress_controller.move_item(
            ProgressState.UPLOADING, ProgressState.UPLOADED, video_id
        )

    for failed_id in failed_ids:
        progress_controller.move_item(
            ProgressState.UPLOADING, ProgressState.PROCESSED, failed_id
        )
