"""
YouTube Download MCP Server using token.pickle authentication.

This MCP server provides tools for accessing YouTube videos owned by 
the resource owner using token.pickle for authentication.
"""

import base64
import os
import pickle
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server import FastMCP

# Initialize FastMCP server
mcp = FastMCP("YouTube Downloader")

def get_authenticated_service():
    """
    Load credentials from token.pickle (file or environment variable) and return authenticated YouTube service.
    
    Supports two methods:
    1. TOKEN_PICKLE_BASE64 environment variable containing base64-encoded pickle data
    2. token.pickle file in current directory
    
    Returns:
        Authenticated YouTube API service
    """
    creds = None
    
    # Try loading from environment variable first
    token_pickle_b64 = os.environ.get('TOKEN_PICKLE_BASE64')
    if token_pickle_b64:
        try:
            pickle_data = base64.b64decode(token_pickle_b64)
            creds = pickle.loads(pickle_data)
        except Exception as e:
            raise ValueError(f"Failed to load credentials from TOKEN_PICKLE_BASE64: {e}")
    elif os.path.exists("token.pickle"):
        # Fall back to file-based loading
        with open("token.pickle", 'rb') as token:
            creds = pickle.load(token)
    else:
        raise ValueError("No token.pickle found. Set TOKEN_PICKLE_BASE64 env var or provide token.pickle file.")
    
    # Refresh credentials if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Save refreshed credentials back if using file
        if not token_pickle_b64 and os.path.exists("token.pickle"):
            with open("token.pickle", 'wb') as token:
                pickle.dump(creds, token)
    
    if not creds or not creds.valid:
        raise ValueError("Invalid credentials. Please authenticate first.")
    
    return build('youtube', 'v3', credentials=creds)


@mcp.tool()
def download_video(
    video_id: str,
    output_dir: str = "./downloads"
) -> dict[str, Any]:
    """
    Get download information for a YouTube video owned by the authenticated user.
    
    Uses token.pickle for authentication to access videos owned by the resource owner.
    Returns the video metadata and YouTube Studio download URL.
    
    Note: To actually download the video file, you need to:
    1. Use the YouTube Studio interface at: https://studio.youtube.com/video/{video_id}/edit/
    2. Click Options > Download
    
    Args:
        video_id: YouTube video ID or URL
        output_dir: Directory where the video should be saved (informational)
        
    Returns:
        Dictionary with video information and download instructions
    """
    try:
        # Verify authentication
        youtube = get_authenticated_service()
        
        # Get video details to verify ownership/access
        response = youtube.videos().list(
            part='snippet,status,contentDetails',
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
        video_status = video_info['status']['uploadStatus']
        duration = video_info['contentDetails']['duration']
        
        studio_url = f"https://studio.youtube.com/video/{video_id}/edit/"
        
        return {
            "success": True,
            "video_id": video_id,
            "title": video_title,
            "upload_status": video_status,
            "duration": duration,
            "studio_download_url": studio_url,
            "output_dir": output_dir,
            "message": f"Video info retrieved: {video_title}",
            "instructions": "To download: Go to YouTube Studio URL, click Options > Download"
        }
        
    except Exception as e:
        return {
            "success": False,
            "video_id": video_id,
            "error": str(e),
            "message": "Failed to get video information"
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
