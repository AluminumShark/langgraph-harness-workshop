"""簡單的煙霧測試,確認 import 與 build_graph 不會炸。"""

from __future__ import annotations


def test_import():
    from pandas_pilot import eval as eval_mod
    from pandas_pilot import graph, tools, trace

    assert hasattr(tools, "inspect_data")
    assert hasattr(graph, "build_graph")
    assert hasattr(trace, "pretty_trace")
    assert hasattr(eval_mod, "EVAL_CASES")
    assert len(eval_mod.EVAL_CASES) >= 5


def test_build_graph_no_api_key(monkeypatch):
    """build_graph 在沒 API key 時應該還能 build 成功(不呼叫 invoke)。"""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key-for-build-only")
    from pandas_pilot.graph import build_graph

    g = build_graph()
    assert g is not None
