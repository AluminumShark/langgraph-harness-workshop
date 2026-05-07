"""LangGraph Harness Workshop 的 helper functions——給 notebook 跟 tests 共用。"""

from __future__ import annotations

from typing import Any


def pretty_trace(graph: Any, user_message: str) -> None:
    """跑 graph,把每個節點的決策漂亮印出來。

    Args:
        graph: 已經 compile 好的 LangGraph (用 MessagesState 的那種)
        user_message: 要送進 agent 的問題
    """
    inputs = {"messages": [{"role": "user", "content": user_message}]}
    for event in graph.stream(inputs, stream_mode="updates"):
        for node_name, update in event.items():
            print(f"\n[{node_name}]")
            for msg in update.get("messages", []):
                # 如果這個 message 帶 tool_calls,印出工具呼叫
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  → 呼叫工具: {tc['name']}({tc['args']})")
                # 如果這個 message 有文字內容,印出來 (截斷到 150 字避免洗版)
                if hasattr(msg, "content") and msg.content:
                    print(f"  → 訊息: {msg.content[:150]}")


def extract_tool_calls(events: list[dict[str, Any]]) -> list[str]:
    """從一連串的 stream event 中,依序抽出工具呼叫名稱。

    Args:
        events: graph.stream() 回傳的事件列表

    Returns:
        工具呼叫名稱的列表,依呼叫順序排列
    """
    sequence: list[str] = []
    for event in events:
        for _node, update in event.items():
            for msg in update.get("messages", []):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        sequence.append(tc["name"])
    return sequence


def extract_final_text(events: list[dict[str, Any]]) -> str:
    """從 stream event 中抽出 agent 最終的文字回答。

    最後一個有文字 content 的 message 就是 agent 的最終答覆。
    """
    last_text = ""
    for event in events:
        for _node, update in event.items():
            for msg in update.get("messages", []):
                if hasattr(msg, "content") and msg.content and isinstance(msg.content, str):
                    last_text = msg.content
    return last_text
