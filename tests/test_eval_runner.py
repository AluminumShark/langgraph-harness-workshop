"""eval_runner.py 的單元測試——用假的 graph 物件,不打真的 LLM。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langgraph_harness_workshop.eval_runner import (
    EVAL_CASES,
    EvalCase,
    evaluate_one,
    run_eval_suite,
)


@dataclass
class FakeMsg:
    """模仿 LangChain message 的測試用物件。"""

    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FakeGraph:
    """假的 graph——預先安排 stream 要吐出什麼 events。"""

    canned_events: list[dict[str, Any]]

    def stream(self, _inputs: dict[str, Any], stream_mode: str = "updates") -> Any:
        """模仿 LangGraph 的 stream 介面,直接吐預先準備好的 events。"""
        del stream_mode
        return iter(self.canned_events)


def _good_run() -> list[dict[str, Any]]:
    """模擬一次「先 inspect_data 再 run_pandas、最後正確指出 East」的成功跑。"""
    return [
        {
            "chatbot": {
                "messages": [
                    FakeMsg(tool_calls=[{"name": "inspect_data", "args": {"path": "sales.csv"}}])
                ]
            }
        },
        {"tools": {"messages": [FakeMsg(content="Shape: (100, 5) Missing: 8")]}},
        {
            "chatbot": {
                "messages": [
                    FakeMsg(tool_calls=[{"name": "run_pandas", "args": {"path": "sales.csv"}}])
                ]
            }
        },
        {"tools": {"messages": [FakeMsg(content="East: 100\nWest: 300")]}},
        {"chatbot": {"messages": [FakeMsg(content="表現最差的是 East 區")]}},
    ]


def _bad_run_skips_inspect() -> list[dict[str, Any]]:
    """模擬一次「跳過 inspect、答案還夾帶 NaN」的失敗跑。"""
    return [
        {
            "chatbot": {
                "messages": [
                    FakeMsg(tool_calls=[{"name": "run_pandas", "args": {"path": "sales.csv"}}])
                ]
            }
        },
        {"tools": {"messages": [FakeMsg(content="region: NaN ...")]}},
        {"chatbot": {"messages": [FakeMsg(content="最差是 NaN 群組")]}},
    ]


def test_evaluate_one_passes_when_all_checks_satisfied() -> None:
    """成功跑應該三個檢查全部通過,passed=True。"""
    graph = FakeGraph(canned_events=_good_run())
    case = EVAL_CASES[0]

    result = evaluate_one(graph, case)

    assert result["case_id"] == "001_must_inspect_first"
    assert result["passed"] is True
    assert result["checks"]["tool_order"] is True
    assert result["checks"]["no_forbidden"] is True
    assert result["checks"]["has_required"] is True


def test_evaluate_one_fails_when_tool_order_wrong() -> None:
    """跳過 inspect_data 應該被 tool_order 抓到。"""
    graph = FakeGraph(canned_events=_bad_run_skips_inspect())
    case = EVAL_CASES[0]

    result = evaluate_one(graph, case)

    assert result["passed"] is False
    assert result["checks"]["tool_order"] is False
    # 同一次跑也會踩到 no_forbidden (答案有 NaN)
    assert result["checks"]["no_forbidden"] is False


def test_evaluate_one_fails_when_required_keyword_missing() -> None:
    """答案沒提到任何區域名稱應該被 has_required 抓到。"""
    events = [
        {"chatbot": {"messages": [FakeMsg(tool_calls=[{"name": "inspect_data", "args": {}}])]}},
        {"chatbot": {"messages": [FakeMsg(tool_calls=[{"name": "run_pandas", "args": {}}])]}},
        {"chatbot": {"messages": [FakeMsg(content="嗯,大概就那樣吧")]}},
    ]
    graph = FakeGraph(canned_events=events)

    result = evaluate_one(graph, EVAL_CASES[0])

    assert result["checks"]["has_required"] is False
    assert result["passed"] is False


def test_evaluate_one_handles_case_with_only_one_check() -> None:
    """只有 answer_must_contain_one_of 一條規則的 case。"""
    events = [
        {"chatbot": {"messages": [FakeMsg(content="2099 年沒有資料")]}},
    ]
    graph = FakeGraph(canned_events=events)

    result = evaluate_one(graph, EVAL_CASES[1])

    assert result["passed"] is True
    # 只該有一個檢查項
    assert set(result["checks"].keys()) == {"has_required"}


def test_run_eval_suite_aggregates_pass_rate() -> None:
    """run_eval_suite 應該回傳整批跑的 pass rate。"""

    @dataclass
    class TwoRunFakeGraph:
        """每呼叫一次 stream,輪流吐第一份跟第二份 events。"""

        runs: list[list[dict[str, Any]]]
        call_count: int = 0

        def stream(self, _inputs: dict[str, Any], stream_mode: str = "updates") -> Any:
            del stream_mode
            run = self.runs[self.call_count]
            self.call_count += 1
            return iter(run)

    # 兩個 case:第一個成功,第二個 (空年份) 也成功
    empty_year_run = [{"chatbot": {"messages": [FakeMsg(content="2099 年沒有資料")]}}]
    graph = TwoRunFakeGraph(runs=[_good_run(), empty_year_run])

    report = run_eval_suite(graph, EVAL_CASES)

    assert report["pass_rate"] == 1.0
    assert len(report["results"]) == 2


def test_run_eval_suite_handles_empty_cases() -> None:
    """空的 case list 應該回傳 pass_rate=0.0,不爆除以零。"""
    graph = FakeGraph(canned_events=[])
    report = run_eval_suite(graph, [])

    assert report["pass_rate"] == 0.0
    assert report["results"] == []


def test_eval_case_typed_dict_accepts_partial_fields() -> None:
    """EvalCase 是 total=False,只填部分欄位應該也合法。"""
    case: EvalCase = {"id": "x", "query": "y"}
    assert case["id"] == "x"
