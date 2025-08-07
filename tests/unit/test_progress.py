from pathlib import Path
import pytest

from progresslib import ProgressController, ProgressState


def test_reset_progress(progress_controller):
    """
    Test resetting the progress file to its default state."""
    progress_controller.reset_progress()
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
