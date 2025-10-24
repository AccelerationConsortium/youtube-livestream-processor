# Video Processing

This project implements a distributed system for the automated processing of hardware livestreams by accelerating/removing stale video sections. The system is segmented into three sections which can be run on independent machines, downloading, processing, and uploading.

These segments are synced by a common `progress.json` file with filelocks for mutual exclusion.

## Downloading

## Processing

## Uploading

## YouTube Download MCP Server

This project also provides a Model Context Protocol (MCP) server for YouTube video downloading and metadata access. This allows AI agents to download YouTube videos and query metadata programmatically.

### Features

The MCP server provides the following tools:

- **`download_video`**: Download a single YouTube video by URL or ID
- **`get_video_metadata`**: Retrieve comprehensive metadata for a video (title, description, duration, views, etc.)
- **`list_playlists`**: List all playlists from an authenticated YouTube account
- **`list_playlist_videos`**: List all videos in a specific playlist
- **`download_playlist_videos`**: Download multiple videos from a playlist

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Usage

#### Running the MCP Server

Start the MCP server:

```bash
python youtube_download_mcp.py
```

#### Using with Claude Desktop

To configure the MCP server for use with Claude Desktop, add the following to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "youtube-downloader": {
      "command": "python",
      "args": [
        "/path/to/youtube-livestream-processor/youtube_download_mcp.py"
      ]
    }
  }
}
```

Replace `/path/to/youtube-livestream-processor/` with the actual path to this repository.

#### Example Usage

Once configured, you can use the MCP server from Claude or other MCP-compatible clients:

```
# Download a video
"Please download the YouTube video at https://www.youtube.com/watch?v=dQw4w9WgXcQ to ./downloads"

# Get video metadata
"What's the duration and view count of video ID dQw4w9WgXcQ?"

# Download from a playlist
"Download the first 5 videos from playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
```

### Tools API Reference

#### download_video

Downloads a YouTube video using yt-dlp.

**Parameters:**
- `url` (str): YouTube video URL or video ID
- `output_dir` (str): Directory to save the video (default: "./downloads")
- `format` (str): Video format/quality (default: "best")
- `filename_template` (str): Output filename template (default: "%(title)s.%(ext)s")

**Returns:** Dictionary with download status and file path

#### get_video_metadata

Retrieves metadata for a YouTube video without downloading.

**Parameters:**
- `url` (str): YouTube video URL or video ID

**Returns:** Dictionary with comprehensive video metadata including title, description, duration, uploader, view count, likes, tags, etc.

#### list_playlists

Lists all playlists for an authenticated YouTube account.

**Parameters:**
- `youtube_token` (str): OAuth token
- `youtube_refresh_token` (str): OAuth refresh token
- `youtube_token_uri` (str): Token URI
- `youtube_client_id` (str): Client ID
- `youtube_client_secret` (str): Client secret

**Returns:** Dictionary with list of playlists (ID and title)

#### list_playlist_videos

Lists all videos in a specific YouTube playlist.

**Parameters:**
- `playlist_id` (str): YouTube playlist ID
- YouTube OAuth parameters (same as list_playlists)

**Returns:** Dictionary with list of videos (ID and title)

#### download_playlist_videos

Downloads multiple videos from a YouTube playlist.

**Parameters:**
- `playlist_id` (str): YouTube playlist ID
- `output_dir` (str): Directory to save videos (default: "./downloads")
- `format` (str): Video format/quality (default: "best")
- `max_videos` (int): Maximum number of videos to download, 0 for all (default: 0)

**Returns:** Dictionary with download status and statistics

### Requirements

- Python 3.10+
- yt-dlp
- mcp >= 1.9.0
- google-api-python-client (for YouTube Data API access)

### Notes

- The `get_video_metadata` function uses caching to improve performance
- Videos are downloaded using yt-dlp which supports a wide range of formats and quality options
- The YouTube Data API tools require OAuth credentials which can be obtained from the Google Cloud Console
