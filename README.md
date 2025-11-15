# Codebase Genius
## Quick start: run Jac server and call repo_mapper walker

1. Activate env & set PYTHONPATH
```bash
source env/bin/activate
cd /path/to/agentic_codebase_genius
export PYTHONPATH="$PWD:$PYTHONPATH"

export JAC_TOKEN="your_jac_token_here"

export REPO_URL="https://github.com/jaseci-labs/jaseci"   # optional fallback
jac serve BE/repo_mapper.jac

curl -s -X POST "http://localhost:8000/walker/repo_mapper" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JAC_TOKEN" \
  -d '{"fields": {"url": "https://github.com/jaseci-labs/jaseci"}}' | jq .


---

## 6) Where/when to run what

- **Terminal A**: run `jac serve BE/repo_mapper.jac` (server).
- **Terminal B**: run the `curl` request (client) or run the integration pytest (the integration test will attempt to POST to the running server).
- Unit test `tests/test_repo_utils_local_clone.py` can be run anywhere after `PYTHONPATH` is set and **does not** require the Jac server.

---

### Run the Jac repo-mapper walker (HTTP)

1. Start server (Terminal A)
```bash
source env/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
export REPO_URL="https://github.com/jaseci-labs/jaseci"  # optional fallback
jac serve BE/repo_mapper.jac

2. Call walker (Terminal B)
export JAC_TOKEN="<your_jac_token_here>"
curl -s -X POST "http://localhost:8000/walker/repo_mapper" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JAC_TOKEN" \
  -d '{"fields":{"url":"https://github.com/jaseci-labs/jaseci"}}' \
  | jq .

# GenAI-Lab
Generative AI prototypes and projects evolving into real-world applications.
