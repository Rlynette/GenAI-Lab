# utils package initializer (lazy-load submodules to avoid circular imports)
# This exposes "repo_utils" for tests doing: from utils import repo_utils

__all__ = ["repo_utils"]

def __getattr__(name: str):
    """
    Lazy import submodules on attribute access (PEP 562).
    When someone does `from utils import repo_utils` Python will access
    the attribute and trigger this function, which imports the real module.
    """
    if name == "repo_utils":
        import importlib
        m = importlib.import_module(f"{__name__}.repo_utils")
        globals()[name] = m
        return m
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return sorted(list(globals().keys()) + __all__)
