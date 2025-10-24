"""
YouTube Download MCP Server

This MCP server provides tools for downloading YouTube videos and accessing 
YouTube metadata using yt-dlp and the YouTube Data API.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
import tempfile
import subprocess
import json

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import Field

from yt_utils import YoutubeUtils

# Initialize FastMCP server
mcp = FastMCP("YouTube Downloader")


class VideoMetadata:
    """Container for video metadata"""
    
    def __init__(self, info_dict: Dict[str, Any]):
        self.id = info_dict.get("id", "")
        self.title = info_dict.get("title", "")
        self.description = info_dict.get("description", "")
        self.duration = info_dict.get("duration", 0)
        self.uploader = info_dict.get("uploader", "")
        self.upload_date = info_dict.get("upload_date", "")
        self.view_count = info_dict.get("view_count", 0)
        self.like_count = info_dict.get("like_count", 0)
        self.channel_id = info_dict.get("channel_id", "")
        self.channel_url = info_dict.get("channel_url", "")
        self.thumbnail = info_dict.get("thumbnail", "")
        self.categories = info_dict.get("categories", [])
        self.tags = info_dict.get("tags", [])
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "duration": self.duration,
            "uploader": self.uploader,
            "upload_date": self.upload_date,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "channel_id": self.channel_id,
            "channel_url": self.channel_url,
            "thumbnail": self.thumbnail,
            "categories": self.categories,
            "tags": self.tags,
        }


@lru_cache(maxsize=100)
def _get_video_metadata_cached(video_url: str) -> VideoMetadata:
    """
    Get video metadata using yt-dlp (cached).
    
    Args:
        video_url: YouTube video URL or video ID
        
    Returns:
        VideoMetadata object containing video information
    """
    # Ensure we have a full URL
    if not video_url.startswith("http"):
        video_url = f"https://www.youtube.com/watch?v={video_url}"
    
    # Use yt-dlp to extract video info without downloading
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-download", video_url],
        capture_output=True,
        text=True,
        check=True
    )
    
    info_dict = json.loads(result.stdout)
    return VideoMetadata(info_dict)


@mcp.tool()
def download_video(
    url: str = Field(description="The YouTube video URL or video ID to download"),
    output_dir: str = Field(description="Directory to save the downloaded video", default="./downloads"),
    format: str = Field(
        description="Video format/quality (e.g., 'best', 'bestvideo+bestaudio', '720p')",
        default="best"
    ),
    filename_template: str = Field(
        description="Template for output filename (e.g., '%(title)s.%(ext)s')",
        default="%(title)s.%(ext)s"
    )
) -> Dict[str, Any]:
    """
    Download a YouTube video using yt-dlp.
    
    This tool downloads a video from YouTube to the specified directory with
    configurable format and naming options.
    
    Args:
        url: YouTube video URL or video ID
        output_dir: Directory where the video will be saved
        format: Desired video format/quality
        filename_template: Template for the output filename
        
    Returns:
        Dictionary containing download status and file path
    """
    # Ensure we have a full URL
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Construct yt-dlp command
    output_template = str(output_path / filename_template)
    cmd = [
        "yt-dlp",
        "-f", format,
        "-o", output_template,
        url
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output to get the actual filename
        output_lines = result.stdout.strip().split("\n")
        downloaded_file = None
        for line in output_lines:
            if "Destination:" in line or "[download]" in line and "has already been downloaded" in line:
                # Extract filename from output
                parts = line.split()
                if len(parts) > 1:
                    downloaded_file = parts[-1]
                    break
        
        return {
            "success": True,
            "url": url,
            "output_dir": output_dir,
            "file": downloaded_file or "Video downloaded successfully",
            "format": format,
            "message": "Video downloaded successfully"
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "stderr": e.stderr,
            "message": "Failed to download video"
        }


@mcp.tool()
def get_video_metadata(
    url: str = Field(description="The YouTube video URL or video ID")
) -> Dict[str, Any]:
    """
    Retrieve metadata for a YouTube video without downloading it.
    
    This tool fetches comprehensive metadata including title, description,
    duration, uploader information, view count, tags, and more. Useful for
    cross-referencing video information before downloading or for cataloging
    purposes.
    
    Args:
        url: YouTube video URL or video ID
        
    Returns:
        Dictionary containing video metadata
    """
    try:
        metadata = _get_video_metadata_cached(url)
        return {
            "success": True,
            "metadata": metadata.to_dict()
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "message": "Failed to retrieve video metadata"
        }


@mcp.tool()
def list_playlists(
    youtube_token: str = Field(description="YouTube API OAuth token"),
    youtube_refresh_token: str = Field(description="YouTube API OAuth refresh token"),
    youtube_token_uri: str = Field(description="YouTube API token URI"),
    youtube_client_id: str = Field(description="YouTube API client ID"),
    youtube_client_secret: str = Field(description="YouTube API client secret"),
) -> Dict[str, Any]:
    """
    List all playlists for the authenticated YouTube account.
    
    This tool uses the YouTube Data API to retrieve all playlists owned by
    the authenticated user. Useful for browsing available content before
    downloading.
    
    Args:
        youtube_token: OAuth token for YouTube API
        youtube_refresh_token: OAuth refresh token
        youtube_token_uri: Token URI for OAuth
        youtube_client_id: YouTube API client ID
        youtube_client_secret: YouTube API client secret
        
    Returns:
        Dictionary containing list of playlists with IDs and titles
    """
    try:
        ytlib = YoutubeUtils(
            youtube_token=youtube_token,
            youtube_refresh_token=youtube_refresh_token,
            youtube_token_uri=youtube_token_uri,
            youtube_client_id=youtube_client_id,
            youtube_client_secret=youtube_client_secret,
        )
        
        playlists = ytlib.get_playlists()
        
        return {
            "success": True,
            "playlists": [
                {"id": playlist.id, "title": playlist.title}
                for playlist in playlists
            ],
            "count": len(playlists)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve playlists"
        }


@mcp.tool()
def list_playlist_videos(
    playlist_id: str = Field(description="The YouTube playlist ID"),
    youtube_token: str = Field(description="YouTube API OAuth token"),
    youtube_refresh_token: str = Field(description="YouTube API OAuth refresh token"),
    youtube_token_uri: str = Field(description="YouTube API token URI"),
    youtube_client_id: str = Field(description="YouTube API client ID"),
    youtube_client_secret: str = Field(description="YouTube API client secret"),
) -> Dict[str, Any]:
    """
    List all videos in a specific YouTube playlist.
    
    This tool retrieves all videos from a given playlist using the YouTube
    Data API. Returns video IDs and titles for each video in the playlist.
    
    Args:
        playlist_id: YouTube playlist ID
        youtube_token: OAuth token for YouTube API
        youtube_refresh_token: OAuth refresh token
        youtube_token_uri: Token URI for OAuth
        youtube_client_id: YouTube API client ID
        youtube_client_secret: YouTube API client secret
        
    Returns:
        Dictionary containing list of videos with IDs and titles
    """
    try:
        ytlib = YoutubeUtils(
            youtube_token=youtube_token,
            youtube_refresh_token=youtube_refresh_token,
            youtube_token_uri=youtube_token_uri,
            youtube_client_id=youtube_client_id,
            youtube_client_secret=youtube_client_secret,
        )
        
        # Create a playlist object
        playlist = YoutubeUtils.Playlist(id=playlist_id, title="")
        videos = ytlib.list_videos_in_playlist(playlist)
        
        return {
            "success": True,
            "playlist_id": playlist_id,
            "videos": [
                {"id": video.id, "title": video.title}
                for video in videos
            ],
            "count": len(videos)
        }
    except Exception as e:
        return {
            "success": False,
            "playlist_id": playlist_id,
            "error": str(e),
            "message": "Failed to retrieve playlist videos"
        }


@mcp.tool()
def download_playlist_videos(
    playlist_id: str = Field(description="The YouTube playlist ID"),
    output_dir: str = Field(description="Directory to save the downloaded videos", default="./downloads"),
    format: str = Field(
        description="Video format/quality (e.g., 'best', 'bestvideo+bestaudio', '720p')",
        default="best"
    ),
    max_videos: int = Field(
        description="Maximum number of videos to download from the playlist (0 for all)",
        default=0
    )
) -> Dict[str, Any]:
    """
    Download multiple videos from a YouTube playlist.
    
    This tool downloads videos from a specified playlist using yt-dlp.
    Can limit the number of videos downloaded if desired.
    
    Args:
        playlist_id: YouTube playlist ID
        output_dir: Directory where videos will be saved
        format: Desired video format/quality
        max_videos: Maximum number of videos to download (0 = all)
        
    Returns:
        Dictionary containing download status and statistics
    """
    # Ensure we have a full playlist URL
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Construct yt-dlp command
    output_template = str(output_path / "%(title)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", format,
        "-o", output_template,
    ]
    
    if max_videos > 0:
        cmd.extend(["--playlist-end", str(max_videos)])
    
    cmd.append(playlist_url)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "success": True,
            "playlist_id": playlist_id,
            "playlist_url": playlist_url,
            "output_dir": output_dir,
            "format": format,
            "max_videos": max_videos if max_videos > 0 else "all",
            "message": "Playlist videos downloaded successfully"
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "playlist_id": playlist_id,
            "error": str(e),
            "stderr": e.stderr,
            "message": "Failed to download playlist videos"
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
