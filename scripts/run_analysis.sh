#!/usr/bin/env bash
set -euo pipefail
REPO_PATH="${1:-.}"
OUT_CCG="/tmp/ccg.json"
OUT_MD="${2:-/tmp/docs.md}"
python - <<PY
from py_module import code_analyzer as ca, docgenie as dg
import json, sys
repo = "$REPO_PATH"
ccg = ca.analyze_ccg(repo)
open("$OUT_CCG","w").write(json.dumps(ccg, indent=2))
md = dg.generate_markdown(repo, ccg, None, "$OUT_MD")
print("Wrote:", "$OUT_CCG", "$OUT_MD")
PY
