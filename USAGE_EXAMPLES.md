# YouTube Download MCP Server - Usage Examples

This document provides detailed examples of how to use the YouTube Download MCP Server with AI agents and programmatically.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Tool Examples](#tool-examples)
3. [Integration with AI Agents](#integration-with-ai-agents)
4. [Advanced Use Cases](#advanced-use-cases)

## Basic Setup

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Or install the package
pip install -e .
```

### Running the Server

```bash
# Start the MCP server
python youtube_download_mcp.py
```

The server will listen for MCP requests over stdio (standard input/output).

## Tool Examples

### 1. Download a Single Video

**Natural Language Request (via AI agent):**
```
"Please download the YouTube video at https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Tool Call Parameters:**
```json
{
  "tool": "download_video",
  "parameters": {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "output_dir": "./downloads",
    "format": "best",
    "filename_template": "%(title)s.%(ext)s"
  }
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "output_dir": "./downloads",
  "file": "Rick Astley - Never Gonna Give You Up.mp4",
  "format": "best",
  "message": "Video downloaded successfully"
}
```

### 2. Get Video Metadata

**Natural Language Request:**
```
"What's the title, duration, and view count of the video with ID dQw4w9WgXcQ?"
```

**Tool Call Parameters:**
```json
{
  "tool": "get_video_metadata",
  "parameters": {
    "url": "dQw4w9WgXcQ"
  }
}
```

**Response:**
```json
{
  "success": true,
  "metadata": {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "description": "The official video for "Never Gonna Give You Up"...",
    "duration": 212,
    "uploader": "Rick Astley",
    "upload_date": "20091025",
    "view_count": 1500000000,
    "like_count": 15000000,
    "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
    "tags": ["Rick Astley", "Never Gonna Give You Up", "80s"],
    "categories": ["Music"]
  }
}
```

### 3. List Playlists

**Natural Language Request:**
```
"Show me all my YouTube playlists"
```

**Tool Call Parameters:**
```json
{
  "tool": "list_playlists",
  "parameters": {
    "youtube_token": "your-oauth-token",
    "youtube_refresh_token": "your-refresh-token",
    "youtube_token_uri": "https://oauth2.googleapis.com/token",
    "youtube_client_id": "your-client-id",
    "youtube_client_secret": "your-client-secret"
  }
}
```

**Response:**
```json
{
  "success": true,
  "playlists": [
    {
      "id": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
      "title": "My Favorite Videos"
    },
    {
      "id": "PLxyz123456789abcdef",
      "title": "Watch Later"
    }
  ],
  "count": 2
}
```

### 4. List Videos in a Playlist

**Natural Language Request:**
```
"What videos are in my 'Watch Later' playlist?"
```

**Tool Call Parameters:**
```json
{
  "tool": "list_playlist_videos",
  "parameters": {
    "playlist_id": "PLxyz123456789abcdef",
    "youtube_token": "your-oauth-token",
    "youtube_refresh_token": "your-refresh-token",
    "youtube_token_uri": "https://oauth2.googleapis.com/token",
    "youtube_client_id": "your-client-id",
    "youtube_client_secret": "your-client-secret"
  }
}
```

**Response:**
```json
{
  "success": true,
  "playlist_id": "PLxyz123456789abcdef",
  "videos": [
    {
      "id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up"
    },
    {
      "id": "abc123xyz789",
      "title": "Another Video Title"
    }
  ],
  "count": 2
}
```

### 5. Download Playlist Videos

**Natural Language Request:**
```
"Download the first 5 videos from playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
```

**Tool Call Parameters:**
```json
{
  "tool": "download_playlist_videos",
  "parameters": {
    "playlist_id": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    "output_dir": "./downloads",
    "format": "best",
    "max_videos": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "playlist_id": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
  "playlist_url": "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
  "output_dir": "./downloads",
  "format": "best",
  "max_videos": 5,
  "message": "Playlist videos downloaded successfully"
}
```

## Integration with AI Agents

### Claude Desktop

1. Copy the example configuration:
   ```bash
   cp claude_desktop_config.example.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Edit the file and update the paths and credentials

3. Restart Claude Desktop

4. Use natural language commands like:
   - "Download the latest Python tutorial from YouTube"
   - "Get metadata for video ID xyz123"
   - "Show me my YouTube playlists"

### Cursor IDE

Add to your Cursor settings:

```json
{
  "mcp.servers": {
    "youtube-downloader": {
      "command": "python",
      "args": ["/path/to/youtube_download_mcp.py"]
    }
  }
}
```

### Other MCP Clients

The server uses stdio transport and follows the MCP specification. It should work with any MCP-compatible client.

## Advanced Use Cases

### 1. Cross-Reference Video Metadata

**Scenario:** Download only videos longer than 10 minutes from a playlist

```
"List videos from playlist XYZ, then for each video, check if the duration 
is more than 600 seconds. Download only those that meet this criteria."
```

The AI agent will:
1. Call `list_playlist_videos` to get video IDs
2. Call `get_video_metadata` for each video
3. Filter videos by duration
4. Call `download_video` for matching videos

### 2. Batch Download with Quality Selection

**Scenario:** Download multiple specific videos in 720p

```
"Download these videos in 720p quality: dQw4w9WgXcQ, abc123xyz, def456uvw"
```

The AI agent will:
1. Call `download_video` with `format="best[height<=720]"` for each video ID

### 3. Content Curation

**Scenario:** Find and download videos with specific tags

```
"From my 'Educational' playlist, show me metadata for all videos, 
then download only those tagged with 'Python' or 'Machine Learning'"
```

The AI agent will:
1. Call `list_playlist_videos` with the playlist ID
2. Call `get_video_metadata` for each video
3. Filter by tags
4. Call `download_video` for matching videos

### 4. Download Format Options

Different format strings for various quality levels:

```python
# Best quality (default)
format = "best"

# Best video + best audio, merged
format = "bestvideo+bestaudio"

# Specific resolution
format = "best[height<=720]"  # 720p or lower
format = "best[height<=1080]" # 1080p or lower

# Audio only
format = "bestaudio"

# Specific format codes
format = "137+140"  # 1080p video + m4a audio
```

### 5. Custom Output Templates

Customize how files are named:

```python
# Include video ID
filename_template = "%(id)s-%(title)s.%(ext)s"

# Include upload date
filename_template = "%(upload_date)s-%(title)s.%(ext)s"

# Organized by uploader
filename_template = "%(uploader)s/%(title)s.%(ext)s"

# Include playlist info
filename_template = "%(playlist)s/%(playlist_index)s-%(title)s.%(ext)s"
```

## Error Handling

The MCP server returns structured error responses:

```json
{
  "success": false,
  "url": "https://www.youtube.com/watch?v=invalid",
  "error": "Video not available",
  "message": "Failed to download video"
}
```

Common error scenarios:
- Invalid URL or video ID
- Video not available (private, deleted, or geo-restricted)
- Network connection issues
- Insufficient disk space
- Invalid OAuth credentials for API calls

## Performance Tips

1. **Use caching**: The `get_video_metadata` function caches results to avoid redundant API calls

2. **Batch operations**: When downloading multiple videos, use `download_playlist_videos` instead of individual `download_video` calls

3. **Format selection**: Choose appropriate formats to balance quality and download time

4. **Parallel downloads**: The MCP server can handle concurrent requests from AI agents

## Security Considerations

1. **OAuth Credentials**: Never commit OAuth tokens to version control. Use environment variables or secure credential stores.

2. **Output Directory**: Ensure the output directory has appropriate permissions and is not exposed publicly.

3. **Video Content**: Be aware of copyright and licensing when downloading videos.

4. **Rate Limiting**: The YouTube Data API has quota limits. Monitor your usage to avoid hitting limits.

## Troubleshooting

### Server Won't Start

```bash
# Check if all dependencies are installed
pip install -r requirements.txt

# Verify Python version (3.10+)
python --version

# Test syntax
python test_syntax.py
```

### Download Fails

```bash
# Test yt-dlp directly
yt-dlp --version
yt-dlp https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Check network connectivity
ping youtube.com
```

### API Authentication Errors

- Verify OAuth credentials are correct
- Check if tokens have expired and need refresh
- Ensure the YouTube Data API is enabled in Google Cloud Console

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Claude Desktop MCP Guide](https://modelcontextprotocol.io/clients/claude-desktop)
