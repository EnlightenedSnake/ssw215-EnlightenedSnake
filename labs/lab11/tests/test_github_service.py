from unittest.mock import MagicMock, patch

from github_service import fetch_repository_readme


def test_fetch_repository_readme_truncates_to_4000_characters():
    response = MagicMock()
    response.status_code = 200
    response.ok = True
    response.text = "x" * 5000

    with patch("github_service.requests.get", return_value=response) as mock_get:
        readme = fetch_repository_readme("owner", "repository")

    mock_get.assert_called_once()
    assert len(readme) == 4000