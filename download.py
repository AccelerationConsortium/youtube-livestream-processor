from pathlib import Path

import pyotp
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from progresslib import ProgressController, ProgressState
from yt_utils import YoutubeUtils
from my_secrets import (
    EMAIL,
    PASSWORD,
    TOTP_SECRET,
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    YOUTUBE_REFRESH_TOKEN,
    YOUTUBE_TOKEN,
    YOUTUBE_TOKEN_URI,
    CHANNEL_ID,
)

# Set up TOTP for 2FA
totp = pyotp.TOTP(TOTP_SECRET)

OUTPUT_DIR = Path(__file__).parent / "downloaded_videos"
PROGRESS_FILE = Path(__file__).parent / "progress.json"
progress_controller = ProgressController(PROGRESS_FILE)


def login_google(page):
    page.goto("https://accounts.google.com/")
    page.get_by_role("textbox", name="Email or phone").fill(EMAIL)
    page.get_by_role("button", name="Next").click()
    page.wait_for_selector('input[name="Passwd"]')
    page.get_by_role("textbox", name="Enter your password").fill(PASSWORD)
    page.get_by_role("button", name="Next").click()

    # TOTP if needed
    try:
        page.get_by_role(
            "link", name="Get a verification code from the Google Authenticator app"
        ).wait_for(timeout=5000)
    except PlaywrightTimeoutError:
        print("No TOTP prompt")
        return

    page.get_by_role(
        "link", name="Get a verification code from the Google Authenticator app"
    ).click()
    page.wait_for_selector('input[name="totpPin"]', timeout=5000)
    page.fill('input[name="totpPin"]', totp.now())
    page.get_by_role("button", name="Next").click()
    page.wait_for_url("https://myaccount.google.com/?pli=1", timeout=20000)


def download_video(page, video: YoutubeUtils.Video):
    try:
        print(f"Navigating to video {video.id}...")
        page.goto(f"https://studio.youtube.com/video/{video.id}/edit/", timeout=15000)
        page.get_by_role("button", name="Options").wait_for(timeout=5000)
        page.get_by_role("button", name="Options").click()
        print(f"Opened video {video.id} options.")

        page.get_by_role("menuitem", name="Download").wait_for(timeout=5000)
        with page.expect_download(timeout=10000) as download_info:
            page.get_by_role("menuitem", name="Download").click()
            print(f"Began downloading video {video.id}...")

        download = download_info.value
        OUTPUT_DIR.mkdir(exist_ok=True)
        file_path = OUTPUT_DIR / f"{video.title}.mp4"
        download.save_as(file_path)

        progress_controller.move_item(
            ProgressState.DOWNLOADING, ProgressState.DOWNLOADED, video.id
        )
        print(f"Downloaded: {file_path}")

    except Exception as e:
        print(f"Failed to download video {video.id}: {e}")


if __name__ == "__main__":
    ytlib = YoutubeUtils(
        youtube_token=YOUTUBE_TOKEN,
        youtube_refresh_token=YOUTUBE_REFRESH_TOKEN,
        youtube_token_uri=YOUTUBE_TOKEN_URI,
        youtube_client_id=YOUTUBE_CLIENT_ID,
        youtube_client_secret=YOUTUBE_CLIENT_SECRET,
        channel_id=CHANNEL_ID,
    )

    playlists = ytlib.get_playlists()
    all_yt_videos = []
    for playlist in playlists:
        videos = ytlib.list_videos_in_playlist(playlist)
        all_yt_videos.extend(videos)

    while True:
        progress_controller.lock_file()
        progress_log = progress_controller._load_progress_unlocked()
        existing_video_ids = [
            video_id
            for status in progress_log.keys()
            for video_id in progress_log[status].keys()
        ]
        video_ids_to_download = set(video.id for video in all_yt_videos) - set(
            existing_video_ids
        )
        videos_to_download = [
            video for video in all_yt_videos if video.id in video_ids_to_download
        ]
        if len(videos_to_download) == 0:
            print("No more videos to download.")
            progress_controller.unlock_file()
            exit(0)
        next_video = videos_to_download[0]

        # Create playlist if it doesn't exist
        new_playlist_name = f"PROCESSED {next_video.playlist.title}"
        existing_playlists = ytlib.get_playlists()
        if new_playlist_name not in [playlist.title for playlist in existing_playlists]:
            new_playlist = ytlib.create_playlist(new_playlist_name)
        else:
            new_playlist = next(
                playlist
                for playlist in existing_playlists
                if playlist.name == new_playlist_name
            )

        progress_controller.add_item(
            ProgressState.DOWNLOADING,
            next_video.id,
            ProgressController.ProgressItem(
                original_video_name=ytlib.video_title_from_id(next_video.id),  # type: ignore
                new_video_name=f"PROCESSED {ytlib.video_title_from_id(next_video.id)}",
                original_playlist_name=next_video.playlist.title,
                new_playlist_name=new_playlist.title,
                original_video_id=next_video.id,
                original_playlist_id=next_video.playlist.id,
                new_playlist_id=new_playlist.id,
            ),
        )
        progress_controller.unlock_file()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            login_google(page)

            download_video(page, next_video)

            browser.close()
