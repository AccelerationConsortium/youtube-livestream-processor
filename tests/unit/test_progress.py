import json
from progresslib import ProgressController, ProgressState


def test_reset_progress(progress_controller):
    # Test resetting the progress to default state
    progress_controller.reset_progress()
    progress_data = progress_controller.load_progress()

    assert progress_data == progress_controller.default_progress


def test_load_progress_empty(progress_controller):
    # Test loading progress when no data exists
    progress_data = progress_controller.load_progress()
    assert progress_data == progress_controller.default_progress


def test_add_item(progress_controller):
    # Test adding a new item to the progress
    progress_controller.add_item(
        ProgressState.DOWNLOADING,
        "video1",
        ProgressController.ProgressItem(
            original_video_name="Test Video 1",
            new_video_name="PROCESSED Test Video 1",
            original_playlist_name="Test Playlist",
            new_playlist_name="PROCESSED Test Playlist",
            original_video_id="123",
            original_playlist_id="456",
            new_playlist_id="789",
        ),
    )

    progress_data = progress_controller.load_progress()
    assert "video1" in progress_data[ProgressState.DOWNLOADING]
    item = progress_data[ProgressState.DOWNLOADING]["video1"]
    assert item.original_video_name == "Test Video 1"
    assert item.new_video_name == "PROCESSED Test Video 1"
    assert item.original_playlist_name == "Test Playlist"
    assert item.new_playlist_name == "PROCESSED Test Playlist"
    assert item.original_video_id == "123"
    assert item.original_playlist_id == "456"
    assert item.new_playlist_id == "789"


def test_load_progress_with_data(progress_controller):
    # Test loading progress when data exists
    to_add = ProgressController.ProgressItem(
        original_video_name="Test Video 1",
        new_video_name="PROCESSED Test Video 1",
        original_playlist_name="Test Playlist",
        new_playlist_name="PROCESSED Test Playlist",
        original_video_id="123",
        original_playlist_id="456",
        new_playlist_id="789",
    )
    progress_controller.add_item(ProgressState.DOWNLOADING, "video1", to_add)

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.DOWNLOADING]["video1"] == to_add


def test_move_item(progress_controller):
    # Test moving an item from one state to another
    progress_controller.add_item(
        ProgressState.DOWNLOADING,
        "video1",
        ProgressController.ProgressItem(
            original_video_name="Test Video 1",
            new_video_name="PROCESSED Test Video 1",
            original_playlist_name="Test Playlist",
            new_playlist_name="PROCESSED Test Playlist",
            original_video_id="123",
            original_playlist_id="456",
            new_playlist_id="789",
        ),
    )

    progress_controller.move_item(
        ProgressState.DOWNLOADING, ProgressState.DOWNLOADED, "video1"
    )

    progress_data = progress_controller.load_progress()
    assert "video1" in progress_data[ProgressState.DOWNLOADED]
    item = progress_data[ProgressState.DOWNLOADED]["video1"]
    assert item.original_video_name == "Test Video 1"
    assert item.new_video_name == "PROCESSED Test Video 1"


def test_read_advance(progress_controller):
    # Test reading and advancing an item from one state to another
    to_add = ProgressController.ProgressItem(
        original_video_name="Test Video 1",
        new_video_name="PROCESSED Test Video 1",
        original_playlist_name="Test Playlist",
        new_playlist_name="PROCESSED Test Playlist",
        original_video_id="123",
        original_playlist_id="456",
        new_playlist_id="789",
    )
    progress_controller.add_item(ProgressState.DOWNLOADING, "video1", to_add)

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.DOWNLOADING, ProgressState.DOWNLOADED
    )

    assert key == "video1"
    assert item == to_add

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.DOWNLOADED, ProgressState.PROCESSING
    )

    assert key == "video1"
    assert item == to_add

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.PROCESSING, ProgressState.PROCESSED
    )

    assert key == "video1"
    assert item == to_add

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.PROCESSED, ProgressState.UPLOADING
    )

    assert key == "video1"
    assert item == to_add

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.UPLOADING, ProgressState.UPLOADED
    )

    assert key == "video1"
    assert item == to_add
