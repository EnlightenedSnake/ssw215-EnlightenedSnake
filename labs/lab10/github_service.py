import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()


class RepositoryNotFoundError(Exception):
    pass


class GitHubUnavailableError(Exception):
    pass


def fetch_repository_readme(owner: str, repository: str) -> str:
    headers = {"Accept": "application/vnd.github.raw"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = (
        "https://api.github.com/repos/"
        f"{quote(owner, safe='')}/{quote(repository, safe='')}/readme"
    )
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as error:
        raise GitHubUnavailableError("GitHub could not be reached") from error

    if response.status_code == 404:
        raise RepositoryNotFoundError("Repository or README not found")
    if not response.ok:
        raise GitHubUnavailableError("GitHub could not fetch the README")

    return response.text[:4000]
