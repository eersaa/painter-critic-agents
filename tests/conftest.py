import pytest


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Returns a non-existent output directory path for save tests."""
    return tmp_path / "output"


@pytest.fixture
def api_url_env(monkeypatch):
    """Sets API_URL to a test value, isolating from real .env."""
    url = "https://test.example.com/v1"
    monkeypatch.setenv("API_URL", url)
    return url
