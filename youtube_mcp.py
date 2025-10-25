"""
YouTube Download MCP Server using token.pickle authentication.

This MCP server provides tools for accessing YouTube videos owned by 
the resource owner using token.pickle for authentication.
"""

import base64
import os
import pickle
from pathlib import Path
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server import FastMCP

# Try to import Playwright (optional)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    import pyotp
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

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


@mcp.tool()
def download_video_playwright(
    video_id: str,
    output_dir: str = "./downloads",
    email: Optional[str] = None,
    password: Optional[str] = None,
    totp_secret: Optional[str] = None,
    headless: bool = True
) -> dict[str, Any]:
    """
    Download a YouTube video using Playwright to automate YouTube Studio.
    
    This is an optional method that uses browser automation to download videos.
    Falls back to download_video if Playwright is not available or credentials are missing.
    
    Requires environment variables or parameters:
    - GOOGLE_EMAIL or email parameter
    - GOOGLE_PASSWORD or password parameter
    - GOOGLE_TOTP_SECRET or totp_secret parameter (for 2FA)
    
    Args:
        video_id: YouTube video ID
        output_dir: Directory to save the downloaded video
        email: Google account email (optional, uses GOOGLE_EMAIL env var if not provided)
        password: Google account password (optional, uses GOOGLE_PASSWORD env var if not provided)
        totp_secret: TOTP secret for 2FA (optional, uses GOOGLE_TOTP_SECRET env var if not provided)
        headless: Run browser in headless mode (default: True)
        
    Returns:
        Dictionary with download status and file path
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            "success": False,
            "error": "Playwright not available. Install with: pip install playwright && playwright install chromium",
            "message": "Use download_video instead for metadata-only access"
        }
    
    # Get credentials from environment or parameters
    email = email or os.environ.get('GOOGLE_EMAIL')
    password = password or os.environ.get('GOOGLE_PASSWORD')
    totp_secret = totp_secret or os.environ.get('GOOGLE_TOTP_SECRET')
    
    if not email or not password:
        return {
            "success": False,
            "error": "Missing Google credentials. Set GOOGLE_EMAIL and GOOGLE_PASSWORD environment variables.",
            "message": "Use download_video instead for metadata-only access"
        }
    
    try:
        # First get video info via API
        youtube = get_authenticated_service()
        response = youtube.videos().list(
            part='snippet',
            id=video_id
        ).execute()
        
        if not response.get('items'):
            return {
                "success": False,
                "error": "Video not found or not accessible",
                "video_id": video_id
            }
        
        video_title = response['items'][0]['snippet']['title']
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Use Playwright to download
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            
            # Login to Google
            try:
                page.goto("https://accounts.google.com/", timeout=15000)
                page.get_by_role("textbox", name="Email or phone").fill(email)
                page.get_by_role("button", name="Next").click()
                page.wait_for_selector('input[name="Passwd"]', timeout=10000)
                page.get_by_role("textbox", name="Enter your password").fill(password)
                page.get_by_role("button", name="Next").click()
                
                # Handle TOTP if needed
                if totp_secret:
                    try:
                        page.get_by_role(
                            "link", name="Get a verification code from the Google Authenticator app"
                        ).wait_for(timeout=5000)
                        page.get_by_role(
                            "link", name="Get a verification code from the Google Authenticator app"
                        ).click()
                        page.wait_for_selector('input[name="totpPin"]', timeout=5000)
                        totp = pyotp.TOTP(totp_secret)
                        page.fill('input[name="totpPin"]', totp.now())
                        page.get_by_role("button", name="Next").click()
                    except PlaywrightTimeoutError:
                        pass  # No TOTP prompt
                
                # Wait for login to complete
                page.wait_for_timeout(2000)
                
            except Exception as e:
                browser.close()
                return {
                    "success": False,
                    "error": f"Login failed: {str(e)}",
                    "message": "Check credentials or use download_video for metadata-only access"
                }
            
            # Navigate to YouTube Studio and download
            try:
                page.goto(f"https://studio.youtube.com/video/{video_id}/edit/", timeout=15000)
                page.get_by_role("button", name="Options").wait_for(timeout=5000)
                page.get_by_role("button", name="Options").click()
                
                page.get_by_role("menuitem", name="Download").wait_for(timeout=5000)
                with page.expect_download(timeout=30000) as download_info:
                    page.get_by_role("menuitem", name="Download").click()
                
                download = download_info.value
                file_path = output_path / f"{video_title}.mp4"
                download.save_as(str(file_path))
                
                browser.close()
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "title": video_title,
                    "file_path": str(file_path),
                    "output_dir": output_dir,
                    "message": f"Successfully downloaded: {video_title}"
                }
                
            except Exception as e:
                browser.close()
                return {
                    "success": False,
                    "video_id": video_id,
                    "error": f"Download failed: {str(e)}",
                    "message": "YouTube Studio may be inaccessible or video not downloadable. Use download_video for metadata."
                }
    
    except Exception as e:
        return {
            "success": False,
            "video_id": video_id,
            "error": str(e),
            "message": "Failed to download video"
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
