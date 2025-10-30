import os
import requests
import json
import pytest

BASE = "http://localhost:8000"
TOKEN = os.environ.get("JAC_TOKEN", "")

@pytest.mark.skipif(not TOKEN, reason="set JAC_TOKEN env var to run integration test")
def test_repo_mapper_walker_runs():
    """
    Integration test that hits the Jac walker endpoint.
    Requires:
      - jac serve BE/repo_mapper.jac running locally
      - JAC_TOKEN exported in the environment
    """
    url = f"{BASE}/walker/repo_mapper"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    # The server expects walker input fields under "fields"
    payload = {"fields": {"url": "https://github.com/jaseci-labs/jaseci"}}

    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)

    # Assert status
    assert r.status_code == 200, f"Unexpected status: {r.status_code}, body={r.text}"

    data = r.json()

    # Basic structure checks
    assert "reports" in data, "Response missing 'reports' key"
    rep = data["reports"]
    assert isinstance(rep, list) and len(rep) >= 1, "Expected non-empty reports list"
    first = rep[0][0]
    assert "cloned_path" in first, f"Missing 'cloned_path' in {first.keys()}"
