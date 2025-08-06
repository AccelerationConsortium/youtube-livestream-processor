import json
from filelock import FileLock
from dataclasses import dataclass


class ProgressController:
    def __init__(self, progress_file_path):
        self.progress_file_path = progress_file_path
        self.lock = FileLock(progress_file_path.with_suffix(".lock"))

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

    def lock_file(self):
        self.lock.acquire()

    def unlock_file(self):
        self.lock.release()

    def load_progress(self) -> dict[str, dict[str, ProgressItem]]:
        with self.lock:
            return self._load_progress_unlocked()

    def _load_progress_unlocked(self) -> dict[str, dict[str, ProgressItem]]:
        if self.progress_file_path.exists():
            with open(self.progress_file_path, "r") as f:
                return json.load(f, object_hook=self.custom_decoder)
        return {}

    def move_item(self, original_state, new_state, key):
        with self.lock:
            if self.progress_file_path.exists():
                with open(self.progress_file_path, "r") as f:
                    progress_data = json.load(f, object_hook=self.custom_decoder)
            else:
                progress_data = {}

            progress_data[new_state][key] = progress_data[original_state][key]
            del progress_data[original_state][key]

            with open(self.progress_file_path, "w") as f:
                json.dump(progress_data, f, cls=self.CustomEncoder)

    def read_and_move_next_item(
        self, original_state, new_state
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
                json.dump(progress_data, f, cls=self.CustomEncoder)

        return key, value

    def add_item(self, state, key, value: ProgressItem):
        with self.lock:
            self._add_item_unlocked(state, key, value)

    def _add_item_unlocked(self, state, key, value: ProgressItem) -> None:
        if self.progress_file_path.exists():
            with open(self.progress_file_path, "r") as f:
                progress_data = json.load(f, object_hook=self.custom_decoder)
        else:
            progress_data = {}

        progress_data.setdefault(state, {})[key] = value

        with open(self.progress_file_path, "w") as f:
            json.dump(progress_data, f, cls=self.CustomEncoder)
