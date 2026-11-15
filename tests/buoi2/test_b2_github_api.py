"""Buoi 2 - B2.13 GitHub REST API (syllabus 6.2).

Same APIRequestContext you used for Toolshop, on a different, real public API.
Fixture: github (see conftest.py). Docs: https://docs.github.com/en/rest

Rate limit: without a token GitHub allows 60 calls per hour per IP address. The whole class shares
the school's IP, so create a token (github.com > Settings > Developer settings > Fine-grained tokens,
no permissions needed) and put it in .env as GITHUB_TOKEN. Never commit .env.

Run:  pytest tests/buoi2/test_b2_github_api.py -v
"""
import uuid  # noqa: F401  (you will need it)

import pytest

pytestmark = [pytest.mark.api, pytest.mark.github]

REPO = "microsoft/playwright-python"


# ---------------------------------------------------------------- B2.13a
def test_b2_13a_github_repo_returns_expected_metadata(github):
    """Goal: GET /repos/{owner}/{repo} describes the repository.
    Precondition: the repository is public.
    Expected: 200, full_name equals REPO, language Python, licence spdx_id Apache-2.0,
    stargazers_count is an int > 0, archived is False."""
    
    response = github.get(f"/repos/{REPO}")

    assert response.status == 200, response.text()

    body = response.json()

    assert body["full_name"] == REPO
    assert body["language"] == "Python"
    assert body["license"]["spdx_id"] == "Apache-2.0"

    assert isinstance(body["stargazers_count"], int)
    assert body["stargazers_count"] > 0

    assert body["archived"] is False



# ---------------------------------------------------------------- B2.13b
def test_b2_13b_github_unknown_user_returns_404_with_message(github):
    """Goal: GitHub explains missing resources.
    Precondition: a login that cannot exist (use uuid).
    Expected: 404 and the JSON message 'Not Found'."""
    
    username = f"nonexistent-{uuid.uuid4().hex}"

    response = github.get(f"/users/{username}")

    assert response.status == 404, response.text()

    body = response.json()

    assert body["message"] == "Not Found"



# ---------------------------------------------------------------- B2.13c
def test_b2_13c_github_response_reports_rate_limit(github):
    """Goal: responses carry rate-limit headers.
    Precondition: none. Use GET /rate_limit: it does not count against your limit.
    Expected: headers x-ratelimit-limit and x-ratelimit-remaining are integers and remaining <= limit.
    Hint: response.headers is a dict with lower-case keys."""
    
    response = github.get("/rate_limit")

    assert response.status == 200, response.text()

    headers = response.headers

    limit = int(headers["x-ratelimit-limit"])
    remaining = int(headers["x-ratelimit-remaining"])

    assert limit > 0
    assert 0 <= remaining <= limit



# ---------------------------------------------------------------- B2.13d (challenge)
def test_b2_13d_github_latest_release_matches_installed_playwright(github):
    """Goal: connect an API answer to something you can check locally.
    Precondition: playwright installed from requirements.txt.
    Expected: GET /repos/{REPO}/releases/latest has tag_name like v1.64.1, not older than
    importlib.metadata.version("playwright")."""
    
    import re
    from importlib.metadata import version
    from packaging.version import Version

    # Goi GitHub API lay ban phat hanh moi nhat
    response = github.get(f"/repos/{REPO}/releases/latest")

    assert response.status == 200, response.text()

    body = response.json()

    # Lay phien ban moi nhat tren GitHub
    tag_name = body["tag_name"]

    assert re.fullmatch(r"v\d+\.\d+\.\d+", tag_name)

    latest_version = Version(tag_name.removeprefix("v"))

    # Lay phien ban Playwright dang cai tren may
    installed_version = Version(version("playwright"))

    # Kiem tra GitHub khong cu hon ban dang cai
    assert latest_version >= installed_version, (
        f"GitHub: {latest_version}, "
        f"Installed: {installed_version}"
    )
