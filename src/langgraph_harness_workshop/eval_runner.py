"""Eval runner——學員看怎麼用,不用看怎麼實作。"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph_harness_workshop.helpers import extract_final_text, extract_tool_calls


class EvalCase(TypedDict, total=False):
    """一個 eval case 的資料結構。

    每個 case 描述「我認為 agent 應該怎麼做」的機械版本——
    把標準寫成程式可以檢查的規則。
    """

    id: str
    query: str
    must_call_tools_in_order_prefix: list[str]
    answer_must_not_contain: list[str]
    answer_must_contain_one_of: list[str]


# 預設的 eval cases——學員可以依自己抓到的失敗模式繼續加
EVAL_CASES: list[EvalCase] = [
    {
        "id": "001_must_inspect_first",
        "query": "找出表現最差的區域",
        # 第一個工具呼叫一定要是 inspect_data
        "must_call_tools_in_order_prefix": ["inspect_data", "run_pandas"],
        # 最終答案不能包含 NaN (代表沒處理乾淨)
        "answer_must_not_contain": ["NaN", "nan"],
        # 答案要明確指出某個區域
        "answer_must_contain_one_of": ["East", "West", "North", "South"],
    },
    {
        "id": "002_handle_empty_result",
        "query": "找出 2099 年的資料",
        "answer_must_contain_one_of": ["沒有", "找不到", "no data", "無資料"],
    },
]


def evaluate_one(graph: Any, case: EvalCase) -> dict[str, Any]:
    """跑一個 eval case,回傳檢查結果。

    檢查邏輯:
    - 跑 graph 處理 case 的 query
    - 抽出 tool 呼叫順序跟最終答案
    - 對照 case 描述的規則一條一條打勾
    """
    events = list(
        graph.stream(
            {"messages": [{"role": "user", "content": case["query"]}]},
            stream_mode="updates",
        )
    )
    tool_seq = extract_tool_calls(events)
    answer = extract_final_text(events)

    checks: dict[str, bool] = {}
    # 檢查 1:工具呼叫順序是否符合預期 (前綴比對)
    if "must_call_tools_in_order_prefix" in case:
        prefix = case["must_call_tools_in_order_prefix"]
        checks["tool_order"] = tool_seq[: len(prefix)] == prefix
    # 檢查 2:答案不該包含的關鍵字 (大小寫不敏感)
    if "answer_must_not_contain" in case:
        checks["no_forbidden"] = all(
            kw.lower() not in answer.lower() for kw in case["answer_must_not_contain"]
        )
    # 檢查 3:答案至少要包含其中一個關鍵字
    if "answer_must_contain_one_of" in case:
        checks["has_required"] = any(
            kw.lower() in answer.lower() for kw in case["answer_must_contain_one_of"]
        )

    return {
        "case_id": case["id"],
        "passed": all(checks.values()) if checks else False,
        "checks": checks,
    }


def run_eval_suite(graph: Any, cases: list[EvalCase]) -> dict[str, Any]:
    """跑完一整批 eval cases,回傳整體 pass rate 跟細節。

    Args:
        graph: 已經 compile 好的 LangGraph
        cases: eval case 列表 (例如 EVAL_CASES)

    Returns:
        dict 含 pass_rate (0.0–1.0) 跟每個 case 的 results
    """
    results = [evaluate_one(graph, c) for c in cases]
    pass_rate = sum(r["passed"] for r in results) / len(results) if results else 0.0
    return {"pass_rate": pass_rate, "results": results}
