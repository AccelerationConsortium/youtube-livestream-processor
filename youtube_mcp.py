"""
YouTube Download MCP Server using token.pickle authentication.

This MCP server provides tools for downloading YouTube videos owned by 
the resource owner using token.pickle for authentication.
"""

import os
import pickle
import subprocess
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server import FastMCP

# Initialize FastMCP server
mcp = FastMCP("YouTube Downloader")

def get_authenticated_service(token_pickle_path: str = "token.pickle"):
    """
    Load credentials from token.pickle and return authenticated YouTube service.
    
    Args:
        token_pickle_path: Path to the token.pickle file
        
    Returns:
        Authenticated YouTube API service
    """
    creds = None
    
    if os.path.exists(token_pickle_path):
        with open(token_pickle_path, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh credentials if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save refreshed credentials
        with open(token_pickle_path, 'wb') as token:
            pickle.dump(creds, token)
    
    if not creds or not creds.valid:
        raise ValueError("Invalid or missing token.pickle. Please authenticate first.")
    
    return build('youtube', 'v3', credentials=creds)


@mcp.tool()
def download_video(
    video_id: str,
    output_dir: str = "./downloads",
    format: str = "best"
) -> dict[str, Any]:
    """
    Download a YouTube video owned by the authenticated user.
    
    Uses token.pickle for authentication to access videos owned by the resource owner.
    Downloads the video using yt-dlp.
    
    Args:
        video_id: YouTube video ID or URL
        output_dir: Directory to save the downloaded video
        format: Video format/quality (e.g., 'best', 'bestvideo+bestaudio', '720p')
        
    Returns:
        Dictionary with download status and file information
    """
    try:
        # Verify authentication
        youtube = get_authenticated_service()
        
        # Get video details to verify ownership/access
        response = youtube.videos().list(
            part='snippet,status',
            id=video_id
        ).execute()
        
        if not response.get('items'):
            return {
                "success": False,
                "error": "Video not found or not accessible",
                "video_id": video_id
            }
        
        video_info = response['items'][0]
        video_title = video_info['snippet']['title']
        
        # Ensure we have a full URL
        if not video_id.startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            video_url = video_id
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Download using yt-dlp
        output_template = str(output_path / "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-f", format,
            "-o", output_template,
            video_url
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "success": True,
            "video_id": video_id,
            "title": video_title,
            "output_dir": output_dir,
            "format": format,
            "message": f"Successfully downloaded: {video_title}"
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "video_id": video_id,
            "error": f"Download failed: {e.stderr}",
            "message": "Failed to download video"
        }
    except Exception as e:
        return {
            "success": False,
            "video_id": video_id,
            "error": str(e),
            "message": "Failed to download video"
        }


@mcp.tool()
def list_my_videos(max_results: int = 50) -> dict[str, Any]:
    """
    List videos owned by the authenticated user.
    
    Uses token.pickle to authenticate and retrieve videos from the user's channel.
    
    Args:
        max_results: Maximum number of videos to return (default: 50, max: 50)
        
    Returns:
        Dictionary with list of video IDs and titles
    """
    try:
        youtube = get_authenticated_service()
        
        # Get the authenticated user's channel
        channels_response = youtube.channels().list(
            part='contentDetails',
            mine=True
        ).execute()
        
        if not channels_response.get('items'):
            return {
                "success": False,
                "error": "No channel found for authenticated user"
            }
        
        # Get uploads playlist ID
        uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from uploads playlist
        videos = []
        playlistitems_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=min(max_results, 50)
        ).execute()
        
        for item in playlistitems_response.get('items', []):
            videos.append({
                "id": item['snippet']['resourceId']['videoId'],
                "title": item['snippet']['title'],
                "published_at": item['snippet']['publishedAt']
            })
        
        return {
            "success": True,
            "videos": videos,
            "count": len(videos)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list videos"
        }


@mcp.tool()
def list_playlists() -> dict[str, Any]:
    """
    List all playlists owned by the authenticated user.
    
    Uses token.pickle to authenticate and retrieve playlists.
    
    Returns:
        Dictionary with list of playlist IDs and titles
    """
    try:
        youtube = get_authenticated_service()
        
        playlists = []
        request = youtube.playlists().list(
            part='snippet',
            mine=True,
            maxResults=50
        )
        
        while request:
            response = request.execute()
            for item in response.get('items', []):
                playlists.append({
                    "id": item['id'],
                    "title": item['snippet']['title']
                })
            request = youtube.playlists().list_next(request, response)
        
        return {
            "success": True,
            "playlists": playlists,
            "count": len(playlists)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list playlists"
        }


@mcp.tool()
def list_playlist_videos(playlist_id: str) -> dict[str, Any]:
    """
    List all videos in a specific playlist.
    
    Uses token.pickle for authentication.
    
    Args:
        playlist_id: YouTube playlist ID
        
    Returns:
        Dictionary with list of video IDs and titles
    """
    try:
        youtube = get_authenticated_service()
        
        videos = []
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50
        )
        
        while request:
            response = request.execute()
            for item in response.get('items', []):
                videos.append({
                    "id": item['snippet']['resourceId']['videoId'],
                    "title": item['snippet']['title'],
                    "published_at": item['snippet']['publishedAt']
                })
            request = youtube.playlistItems().list_next(request, response)
        
        return {
            "success": True,
            "playlist_id": playlist_id,
            "videos": videos,
            "count": len(videos)
        }
        
    except Exception as e:
        return {
            "success": False,
            "playlist_id": playlist_id,
            "error": str(e),
            "message": "Failed to list playlist videos"
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
