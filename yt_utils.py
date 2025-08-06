import os
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dataclasses import dataclass


YT_API_KEY = os.getenv("YT_API_KEY")


class YoutubeUtils:
    def __init__(
        self,
        youtube_token,
        youtube_refresh_token,
        youtube_token_uri,
        youtube_client_id,
        youtube_client_secret,
    ):
        self.youtube = build(
            "youtube",
            "v3",
            credentials=Credentials(
                token=youtube_token,
                refresh_token=youtube_refresh_token,
                token_uri=youtube_token_uri,
                client_id=youtube_client_id,
                client_secret=youtube_client_secret,
                scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
            ),
        )

    @dataclass
    class Playlist:
        id: str
        title: str

    @dataclass
    class Video:
        id: str
        title: str
        playlist: "YoutubeUtils.Playlist"

    def get_playlists(self):
        playlists = []
        request = self.youtube.playlists().list(
            part="snippet", mine=True, maxResults=50
        )

        while request:
            response = request.execute()
            for item in response.get("items", []):
                playlist_id = item["id"]
                title = item["snippet"]["title"]
                print(f"{title}: {playlist_id}")
                playlists.append(self.Playlist(playlist_id, title))

            request = self.youtube.playlists().list_next(request, response)

        return playlists

    def list_videos_in_playlist(self, playlist: Playlist) -> list[Video]:
        videos = []
        request = self.youtube.playlistItems().list(
            part="snippet", playlistId=playlist.id, maxResults=50
        )

        while request:
            response = request.execute()
            for item in response["items"]:
                video_id = item["snippet"]["resourceId"]["videoId"]
                title = item["snippet"]["title"]
                print(f"  {title}: {video_id}")
                videos.append(self.Video(video_id, title, playlist))

            request = self.youtube.playlistItems().list_next(request, response)

        return videos

    def upload(
        self, file_path, title, description="", category_id="22", privacy="public"
    ):
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": category_id,
            },
            "status": {"privacyStatus": privacy},
        }

        media = MediaFileUpload(
            file_path, chunksize=-1, resumable=True, mimetype="video/*"
        )
        request = self.youtube.videos().insert(
            part="snippet,status", body=body, media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        print(f"Upload complete. Video ID: {response['id']}")

        while True:
            processing_response = (
                self.youtube.videos()
                .list(part="processingDetails", id=response["id"])
                .execute()
            )

            processing_status = (
                processing_response["items"][0]
                .get("processingDetails", {})
                .get("processingStatus", "")
            )

            print(f"Processing status: {processing_status}")
            if processing_status == "succeeded":
                break
            elif processing_status == "failed":
                raise RuntimeError("YouTube processing failed.")
            else:
                time.sleep(5)

        return response

    def add_to_playlist(self, video_id, playlist_id):
        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            }
        }

        request = self.youtube.playlistItems().insert(part="snippet", body=body)
        response = request.execute()
        print(f"Video added to playlist: {response['snippet']['title']}")
        return response

    def id_from_url(self, url: str) -> str:
        if "youtube.com/live/" in url:
            return url.split("/")[-1].split("?")[0]
        elif "youtube.com/watch?v=" in url:
            return url.split("v=")[-1].split("&")[0]
        else:
            raise ValueError("Invalid YouTube URL format")

    def video_title_from_id(self, video_id) -> str | None:
        response = self.youtube.videos().list(part="snippet", id=video_id).execute()

        if response["items"]:
            return response["items"][0]["snippet"]["title"]
        else:
            return None

    def playlist_title_from_id(self, playlist_id):
        response = (
            self.youtube.playlists().list(part="snippet", id=playlist_id).execute()
        )

        if response["items"]:
            return response["items"][0]["snippet"]["title"]
        else:
            return None
