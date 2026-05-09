"""把 graph.stream 的事件流漂亮印出來,方便講師現場 debug。"""

from __future__ import annotations

from typing import Any


def pretty_trace(graph, user_message: str, *, config: dict[str, Any] | None = None) -> list[dict]:
    """跑 graph 並把每個節點的決策即時列印出來。

    參數:
        graph: 已 compile 的 LangGraph
        user_message: 使用者訊息
        config: graph.stream 的 config(可選)
    回傳:
        每個 step 的 raw event(方便後續再分析)
    """
    events: list[dict] = []
    inputs = {"messages": [{"role": "user", "content": user_message}]}

    print(f"USER: {user_message}\n")

    for step, event in enumerate(
        graph.stream(inputs, config=config, stream_mode="updates"),
        start=1,
    ):
        events.append(event)
        for node_name, node_state in event.items():
            print(f"--- step {step} | node: {node_name} ---")
            messages = node_state.get("messages", [])
            for msg in messages:
                _print_message(msg)
            print()

    return events


def _print_message(msg) -> None:
    role = type(msg).__name__
    tool_calls = getattr(msg, "tool_calls", None)

    if tool_calls:
        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", "?")
            args = call.get("args") if isinstance(call, dict) else getattr(call, "args", {})
            print(f"  [{role}] tool_call -> {name}({args})")
    else:
        # 用 .text 統一從 str / list-of-dict content 拿純字串
        text = msg.text if hasattr(msg, "text") else str(getattr(msg, "content", ""))
        if len(text) > 400:
            text = text[:400] + "..."
        print(f"  [{role}] {text}")
