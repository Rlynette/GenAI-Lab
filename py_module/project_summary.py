"""
project_summary

Combine README summarizer + code_analyzer into a single project summary JSON.

Functions:
- generate_project_summary(root=".") -> dict
- CLI: python -m py_module.project_summary summarize <root> [--out out.json]
"""
from pathlib import Path
import json
import importlib
import sys
from typing import Dict, Any

# import our analyzer (should exist)
try:
    from py_module.code_analyzer import analyze_path
except Exception as e:
    raise ImportError("py_module.code_analyzer not found or failed to import. "
                      "Ensure py_module/code_analyzer.py is present.") from e

# Try to import README summariser (two spellings)
_readme_summarizer = None
for mod_name in ("py_module.readme_summarizer", "py_module.readme_summariser", "py_module.readme_summarizer_main"):
    try:
        mod = importlib.import_module(mod_name)
        # prefer function name 'summarize_readme' or 'summarize' if present
        if hasattr(mod, "summarize_readme"):
            _readme_summarizer = mod.summarize_readme
            break
        if hasattr(mod, "summarize"):
            _readme_summarizer = mod.summarize
            break
    except Exception:
        continue

def fallback_readme_summarizer(root: Path) -> Dict[str, Any]:
    """A safe fallback that returns headings and the first paragraph of README.md"""
    readme = root / "README.md"
    if not readme.exists():
        return {"error": "README.md not found", "content": None}
    txt = readme.read_text(encoding="utf-8", errors="ignore")
    # Extract headings (lines starting with #) and first long paragraph
    headings = [line.strip() for line in txt.splitlines() if line.strip().startswith("#")]
    # naive first paragraph (first block of text > 20 chars)
    paras = [p.strip() for p in txt.split("\n\n") if len(p.strip()) > 20]
    first_para = paras[0] if paras else ""
    # short summary: first 200 chars of first paragraph
    short_summary = (first_para[:200] + "...") if len(first_para) > 200 else first_para
    return {"headings": headings, "first_paragraph": first_para, "short_summary": short_summary}

def _call_readme_summarizer(root: Path) -> Dict[str, Any]:
    if _readme_summarizer is None:
        return {"source": "fallback", "summary": fallback_readme_summarizer(root)}
    try:
        # call summarizer — many implementations accept a path or string
        res = _readme_summarizer(str(root))
        # if the imported function returns plain text, wrap it
        if isinstance(res, str):
            return {"source": "external", "summary": {"text": res}}
        return {"source": "external", "summary": res}
    except TypeError:
        # try calling with Path object
        try:
            res = _readme_summarizer(root)
            if isinstance(res, str):
                return {"source": "external", "summary": {"text": res}}
            return {"source": "external", "summary": res}
        except Exception as e:
            return {"source": "external", "error": f"readme summarizer failed: {e}"}
    except Exception as e:
        return {"source": "external", "error": f"readme summarizer failed: {e}"}

def generate_project_summary(root: str = ".") -> Dict[str, Any]:
    root_p = Path(root).resolve()
    code_analysis = analyze_path(str(root_p))
    readme = _call_readme_summarizer(root_p)
    out = {
        "project_root": str(root_p),
        "readme_summary": readme,
        "code_analysis": code_analysis,
    }
    return out

def _cli():
    import argparse
    p = argparse.ArgumentParser(prog="project_summary", description="Combine README summarizer + code analyzer")
    p.add_argument("command", choices=["summarize"], help="summarize the project")
    p.add_argument("root", nargs="?", default=".", help="project root (default: .)")
    p.add_argument("--out", "-o", help="Write JSON summary to a file (default stdout)")
    args = p.parse_args()
    if args.command == "summarize":
        summary = generate_project_summary(args.root)
        if args.out:
            Path(args.out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(f"Wrote summary to {args.out}")
        else:
            print(json.dumps(summary, indent=2))
    else:
        p.print_help()

if __name__ == "__main__":
    _cli()
