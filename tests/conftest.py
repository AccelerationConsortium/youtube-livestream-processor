import pytest
from pathlib import Path
from progresslib import ProgressController


@pytest.fixture
def progress_file(tmp_path) -> Path:
    """Temporary progress file for testing."""
    return tmp_path / "progress.json"


@pytest.fixture
def progress_controller(progress_file):
    """Returns a ProgressController with a temp file."""
    controller = ProgressController(progress_file_path=progress_file)
    controller.reset_progress()
    return controller
