# YouTube Livestream Processor

Downloads YouTube videos from playlists, detects low-motion sections, and uploads processed copies back to YouTube.

<p align="left"><img src="resources/overlay.png" alt="16x speed overlay" width="100"></p>

The pipeline has three independent stages:

1. `download.py` downloads playlist videos.
2. `process.py` marks low-motion sections and applies a 16x speedup.
3. `upload.py` uploads the processed videos and updates playlists.

Shared machines use `progress.json` to coordinate stage transitions. File locks prevent workers from claiming the same item.

## Requirements

- Python 3.11
- Google OAuth credentials for the YouTube Data API
- `ffmpeg` with NVENC support
- `auto-editor`
- `yt-dlp`
- Playwright Chromium

The processing stage requires an NVIDIA GPU because `_edit_add_overlay` uses `h264_nvenc`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Copy `my_secrets_example.py` to `my_secrets.py`, then fill in the YouTube API credentials and Google account fields. Do not commit `my_secrets.py` (add it to `.gitignore` to avoid accidental commits); it contains credentials.

Initialize the progress file before the first run:

```bash
python -c "from progresslib import ProgressController; from pathlib import Path; ProgressController(Path('progress.json')).reset_progress()"
```

## Run

Run the stages on separate terminals or machines that share this repository and `progress.json`:

```bash
python download.py
python process.py
python upload.py
```

Each stage exits when there are no items left in its current state.
