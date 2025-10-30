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

## 7) After you push — next step (code analysis)

Once you have pushed `feature/repo-mapper` and confirmed tests pass locally:

- I will run a quick code-analysis checklist for you (static checks and consistency between your Jac walker and `py_module` helpers), and prepare small improvements if needed (e.g., guard against long clone times, retries, or rate limiting).
- Then we’ll add the integration test as part of CI (optional) and continue to next tasks (README summarizer / code analyzer / packaging).

---

If you want I can now:
1. Produce the exact `git` paste commands for your environment (with your remote URL filled in if you paste it), **or**
2. Wait for you to run the rename + push and report back (I’ll then run the code analysis and create PR checklist + CI test steps).

Which do you want me to do now?
::contentReference[oaicite:0]{index=0}


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


Expected: JSON output containing reports array with cloned_path and tree.

---

# 7 — Git: commit & push your changes (on feature branch)
After making changes (repo_utils.py, tests, README), commit & push from the feature branch:

```bash
git checkout feature/repo-mapper
git add utils/repo_utils.py tests/test_walker_integration.py README.md
git commit -m "Harden repo_utils, add integration test and README curl example"
git push origin feature/repo-mapper


If you changed the branch name locally and want to set upstream:
git push -u origin feature/repo-mapper