import json
from pathlib import Path
from filelock import FileLock
from enum import Enum
from dataclasses import dataclass


class ProgressState(str, Enum):
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"


class ProgressController:
    def __init__(self, progress_file_path: Path):
        self.progress_file_path = progress_file_path
        self.lock = FileLock(progress_file_path.with_suffix(".lock"))
        self.default_progress = {
            ProgressState.DOWNLOADING: {},
            ProgressState.DOWNLOADED: {},
            ProgressState.PROCESSING: {},
            ProgressState.PROCESSED: {},
            ProgressState.UPLOADING: {},
            ProgressState.UPLOADED: {},
        }

    @dataclass
    class ProgressItem:
        original_video_name: str
        new_video_name: str
        original_playlist_name: str
        new_playlist_name: str
        original_video_id: str
        original_playlist_id: str
        new_playlist_id: str

    class CustomEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, ProgressController.ProgressItem):
                return {
                    "__type__": "ProgressItem",
                    "original_video_name": o.original_video_name,
                    "new_video_name": o.new_video_name,
                    "original_playlist_name": o.original_playlist_name,
                    "new_playlist_name": o.new_playlist_name,
                    "original_video_id": o.original_video_id,
                    "original_playlist_id": o.original_playlist_id,
                    "new_playlist_id": o.new_playlist_id,
                }
            return super().default(o)

    def custom_decoder(self, dct):
        if "__type__" in dct and dct["__type__"] == "ProgressItem":
            return self.ProgressItem(
                dct["original_video_name"],
                dct["new_video_name"],
                dct["original_playlist_name"],
                dct["new_playlist_name"],
                dct["original_video_id"],
                dct["original_playlist_id"],
                dct["new_playlist_id"],
            )
        return dct

    def reset_progress(self):
        with self.lock:
            with open(self.progress_file_path, "w") as f:
                json.dump(self.default_progress, f, cls=self.CustomEncoder, indent=4)

    def lock_file(self):
        self.lock.acquire()

    def unlock_file(self):
        self.lock.release()

    def load_progress(self) -> dict[str, dict[str, ProgressItem]]:
        with self.lock:
            if self.progress_file_path.exists():
                with open(self.progress_file_path, "r") as f:
                    return json.load(f, object_hook=self.custom_decoder)
            return {}

    def move_item(
        self, original_state: ProgressState, new_state: ProgressState, key: str
    ):
        with self.lock:
            if self.progress_file_path.exists():
                with open(self.progress_file_path, "r") as f:
                    progress_data = json.load(f, object_hook=self.custom_decoder)
            else:
                progress_data = {}

            progress_data[new_state][key] = progress_data[original_state][key]
            del progress_data[original_state][key]

            with open(self.progress_file_path, "w") as f:
                json.dump(progress_data, f, cls=self.CustomEncoder, indent=4)

    def read_and_move_next_item(
        self, original_state: ProgressState, new_state: ProgressState
    ) -> tuple[str, ProgressItem] | None:
        with self.lock:
            if self.progress_file_path.exists():
                with open(self.progress_file_path, "r") as f:
                    progress_data = json.load(f, object_hook=self.custom_decoder)
            else:
                progress_data = {}

            if not progress_data.get(original_state):
                return None

            key, value = next(iter(progress_data[original_state].items()))
            progress_data[new_state][key] = value
            del progress_data[original_state][key]

            with open(self.progress_file_path, "w") as f:
                json.dump(progress_data, f, cls=self.CustomEncoder, indent=4)

        return key, value

    def add_item(self, state: ProgressState, key: str, value: ProgressItem):
        with self.lock:
            if self.progress_file_path.exists():
                with open(self.progress_file_path, "r") as f:
                    progress_data = json.load(f, object_hook=self.custom_decoder)
            else:
                progress_data = {}

            progress_data.setdefault(state, {})[key] = value

            with open(self.progress_file_path, "w") as f:
                json.dump(progress_data, f, cls=self.CustomEncoder, indent=4)
