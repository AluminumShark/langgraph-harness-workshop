"""簡單的 eval suite,用來檢測 agent 行為是否符合預期。"""

from __future__ import annotations

from typing import Any

# 預設 demo CSV 路徑(學員在 notebook 裡可以改)
DEFAULT_CSV = "data/sales.csv"

EVAL_CASES: list[dict[str, Any]] = [
    {
        "id": "001_must_inspect_first",
        "user_message": f"幫我看一下 {DEFAULT_CSV} 這份資料的概況。",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
    {
        "id": "002_handle_empty_result",
        "user_message": f"在 {DEFAULT_CSV} 裡找出 region 是 'Mars' 的紀錄總數。",
        "must_call_first": "inspect_data",
        "must_contain_in_final": ["0"],
    },
    {
        "id": "003_inspect_before_summary",
        "user_message": f"幫我計算 {DEFAULT_CSV} 的 revenue 平均。",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
    {
        "id": "004_top_region",
        "user_message": f"分析 {DEFAULT_CSV},哪個 region 的平均 revenue 最低?",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
    {
        "id": "005_count_rows",
        "user_message": f"{DEFAULT_CSV} 總共有幾筆資料?",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
]


def extract_tool_calls(events: list[dict]) -> list[str]:
    """從 graph.stream 的 events 裡抽出 tool 呼叫的順序(by name)。"""
    names: list[str] = []
    for event in events:
        for _node, state in event.items():
            for msg in state.get("messages", []) or []:
                tool_calls = getattr(msg, "tool_calls", None) or []
                for call in tool_calls:
                    name = (
                        call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
                    )
                    if name:
                        names.append(name)
    return names


def extract_final_text(events: list[dict]) -> str:
    """抓最後一則由 chatbot 節點產生、且沒有 tool_calls 的訊息文字。"""
    final = ""
    for event in events:
        for node, state in event.items():
            if node != "chatbot":
                continue
            for msg in state.get("messages", []) or []:
                tool_calls = getattr(msg, "tool_calls", None)
                if not tool_calls:
                    # 用 .text 統一處理 gemini-2.5+ 的 list-of-dict content
                    final = msg.text if hasattr(msg, "text") else str(getattr(msg, "content", "") or "")
    return final


def evaluate_one(graph, case: dict[str, Any]) -> dict[str, Any]:
    """跑一個 eval case,回傳 pass / fail 與細節。"""
    inputs = {"messages": [{"role": "user", "content": case["user_message"]}]}
    events = list(graph.stream(inputs, stream_mode="updates"))

    tool_calls = extract_tool_calls(events)
    final_text = extract_final_text(events)

    reasons: list[str] = []
    must_call_first = case.get("must_call_first")
    if must_call_first:
        if not tool_calls:
            reasons.append(f"沒有呼叫任何 tool(預期先呼叫 {must_call_first})")
        elif tool_calls[0] != must_call_first:
            reasons.append(f"第一個 tool 是 {tool_calls[0]},預期 {must_call_first}")

    for keyword in case.get("must_contain_in_final", []):
        if keyword not in final_text:
            reasons.append(f"最終回覆缺少關鍵字:{keyword!r}")

    passed = len(reasons) == 0
    return {
        "id": case["id"],
        "passed": passed,
        "reasons": reasons,
        "tool_calls": tool_calls,
        "final_text": final_text,
    }


def run_eval_suite(graph, cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """跑整個 eval suite,印出彙總後回傳結果。"""
    cases = cases if cases is not None else EVAL_CASES
    results = []
    for case in cases:
        result = evaluate_one(graph, case)
        mark = "PASS" if result["passed"] else "FAIL"
        print(f"[{mark}] {result['id']}  tool_calls={result['tool_calls']}")
        for reason in result["reasons"]:
            print(f"        - {reason}")
        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n通過 {passed}/{total} ({passed / total:.0%})")
    return {"results": results, "passed": passed, "total": total}
