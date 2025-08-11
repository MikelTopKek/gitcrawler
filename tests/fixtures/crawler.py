import tempfile

from pytest import fixture
from src.gitcrawler.models import SearchResult


@fixture
def temp_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@fixture
def sample_json_data():
    """Sample GitHub search JSON response."""
    return {
        "payload": {
            "results": [
                {
                    "repo": {"repository": {"owner_login": "user", "name": "some_repoo"}},
                    "number": 322,
                    "path": "path",
                    "title": "title_name",
                },
                {"repo": {"repository": {"owner_login": "user128001", "name": "repo2"}}, "number": 1123},
            ]
        }
    }


@fixture
def proxy_list():
    """List of proxy strings."""
    return ["192.168.0.1:8000", "10.0.0.1:777"]


@fixture
def search_results():
    """Sample search results."""
    return [
        SearchResult(url="https://github.com/user1/repo1"),
        SearchResult(
            url="https://github.com/user2/repo2", extra={"owner": "user2", "language_stats": {"Python": 80.0}}
        ),
    ]


@fixture
def language_stats() -> int:
    return 90


@fixture
def test_url() -> str:
    return "http://test.com"


@fixture
def test_ip() -> str:
    return "192.168.0.1:8000"


@fixture
def test_url_github_repo() -> str:
    return "https://github.com/user/repo"
