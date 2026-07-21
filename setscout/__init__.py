__all__ = ["build_setscout_graph", "run_pipeline"]


def __getattr__(name: str):
    if name == "build_setscout_graph":
        from setscout.graph import build_setscout_graph

        return build_setscout_graph
    if name == "run_pipeline":
        from setscout.pipeline import run_pipeline

        return run_pipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
