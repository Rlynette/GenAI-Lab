from pathlib import Path
from py_module import code_analyzer as ca

def test_ccg_basic(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    a = repo / "a.py"
    a.write_text('''def train_model(x):\n    return 1\n\ndef caller():\n    train_model(2)\n''', encoding="utf-8")
    b = repo / "b.py"
    b.write_text('''class Model:\n    pass\n\ndef use_model():\n    m = Model()\n''', encoding="utf-8")
    ccg = ca.analyze_ccg(str(repo))
    assert "nodes" in ccg
    callers = ca.find_callers(ccg, "train_model")
    assert isinstance(callers, list)
    mer = ca.ccg_to_mermaid(ccg)
    assert "graph TD" in mer
