import json
from progresslib import ProgressController, ProgressState
import pytest


@pytest.fixture
def dummy_progress_data():
    return "test_video_key", ProgressController.ProgressItem(
        original_video_name="Test Video",
        new_video_name="PROCESSED Test Video",
        original_playlist_name="Test Playlist",
        new_playlist_name="PROCESSED Test Playlist",
        original_video_id="123",
        original_playlist_id="456",
        new_playlist_id="789",
    )


def test_reset_progress(progress_controller):
    # Test resetting the progress to default state
    progress_controller.reset_progress()
    progress_data = progress_controller.load_progress()

    assert progress_data == progress_controller.default_progress


def test_load_progress_empty(progress_controller):
    # Test loading progress when no data exists
    progress_data = progress_controller.load_progress()
    assert progress_data == progress_controller.default_progress


def test_add_item(progress_controller, dummy_progress_data):
    # Test adding a new item to the progress
    dummy_key, dummy_item = dummy_progress_data
    progress_controller.add_item(ProgressState.DOWNLOADING, dummy_key, dummy_item)

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.DOWNLOADING][dummy_key] == dummy_item


def test_load_progress_with_data(progress_controller, dummy_progress_data):
    # Test loading progress when data exists
    dummy_key, dummy_item = dummy_progress_data
    progress_controller.add_item(ProgressState.DOWNLOADING, dummy_key, dummy_item)

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.DOWNLOADING][dummy_key] == dummy_item


def test_move_item(progress_controller, dummy_progress_data):
    # Test moving an item from one state to another
    dummy_key, dummy_item = dummy_progress_data
    progress_controller.add_item(ProgressState.DOWNLOADING, dummy_key, dummy_item)

    progress_controller.move_item(
        ProgressState.DOWNLOADING, ProgressState.DOWNLOADED, dummy_key
    )

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.DOWNLOADED][dummy_key] == dummy_item


def test_read_advance(progress_controller, dummy_progress_data):
    # Test reading and advancing an item from one state to another
    dummy_key, dummy_item = dummy_progress_data
    progress_controller.add_item(ProgressState.DOWNLOADING, dummy_key, dummy_item)

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.DOWNLOADING, ProgressState.DOWNLOADED
    )

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.DOWNLOADED][key] == dummy_item
    assert item == dummy_item
    assert progress_data[ProgressState.DOWNLOADING] == {}

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.DOWNLOADED, ProgressState.PROCESSING
    )

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.PROCESSING][key] == dummy_item
    assert item == dummy_item
    assert progress_data[ProgressState.DOWNLOADED] == {}

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.PROCESSING, ProgressState.PROCESSED
    )

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.PROCESSED][key] == dummy_item
    assert item == dummy_item
    assert progress_data[ProgressState.PROCESSING] == {}

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.PROCESSED, ProgressState.UPLOADING
    )

    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.UPLOADING][key] == dummy_item
    assert item == dummy_item
    assert progress_data[ProgressState.PROCESSED] == {}

    key, item = progress_controller.read_and_move_next_item(
        ProgressState.UPLOADING, ProgressState.UPLOADED
    )

    progress_data = progress_controller.load_progress()
    progress_data = progress_controller.load_progress()
    assert progress_data[ProgressState.UPLOADED][key] == dummy_item
    assert item == dummy_item
    assert progress_data[ProgressState.UPLOADING] == {}


def test_reentrant(progress_controller, dummy_progress_data):
    # Test that the lock is reentrant
    dummy_key, dummy_item = dummy_progress_data

    progress_controller.lock_file()
    progress_controller.add_item(ProgressState.DOWNLOADING, dummy_key, dummy_item)
    progress_controller.unlock_file()

    progress_data = progress_controller.load_progress()

    assert progress_data[ProgressState.DOWNLOADING][dummy_key] == dummy_item
