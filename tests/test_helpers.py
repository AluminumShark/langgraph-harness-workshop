"""helpers.py 的單元測試——不打真的 LLM。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langgraph_harness_workshop.helpers import (
    extract_final_text,
    extract_tool_calls,
)


@dataclass
class FakeMsg:
    """假裝是 LangChain message 的測試用物件。"""

    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


def _event(node: str, msgs: list[FakeMsg]) -> dict[str, Any]:
    """製造一個 stream event,模仿 LangGraph 的 update 結構。"""
    return {node: {"messages": msgs}}


def test_extract_tool_calls_returns_names_in_order() -> None:
    """確認 extract_tool_calls 依序回傳所有工具呼叫名稱。"""
    events = [
        _event(
            "chatbot",
            [
                FakeMsg(
                    tool_calls=[
                        {"name": "inspect_data", "args": {"path": "sales.csv"}},
                    ]
                )
            ],
        ),
        _event("tools", [FakeMsg(content="Shape: (100, 5)")]),
        _event(
            "chatbot",
            [
                FakeMsg(
                    tool_calls=[
                        {"name": "run_pandas", "args": {"path": "sales.csv", "code": "..."}},
                    ]
                )
            ],
        ),
        _event("tools", [FakeMsg(content="region    revenue\nEast  100")]),
        _event("chatbot", [FakeMsg(content="East 區表現最差")]),
    ]

    assert extract_tool_calls(events) == ["inspect_data", "run_pandas"]


def test_extract_tool_calls_empty_when_no_calls() -> None:
    """沒有 tool_calls 時應該回傳空 list。"""
    events = [_event("chatbot", [FakeMsg(content="hello")])]
    assert extract_tool_calls(events) == []


def test_extract_tool_calls_handles_multiple_in_one_message() -> None:
    """同一個 message 帶多個 tool_calls 時要全部抽出來。"""
    events = [
        _event(
            "chatbot",
            [
                FakeMsg(
                    tool_calls=[
                        {"name": "tool_a", "args": {}},
                        {"name": "tool_b", "args": {}},
                    ]
                )
            ],
        ),
    ]
    assert extract_tool_calls(events) == ["tool_a", "tool_b"]


def test_extract_final_text_returns_last_content() -> None:
    """extract_final_text 應該回傳最後一個有 content 的訊息。"""
    events = [
        _event("chatbot", [FakeMsg(content="第一輪")]),
        _event("tools", [FakeMsg(content="工具結果")]),
        _event("chatbot", [FakeMsg(content="最終答案是 East")]),
    ]
    assert extract_final_text(events) == "最終答案是 East"


def test_extract_final_text_empty_when_no_content() -> None:
    """都沒有文字內容時回傳空字串。"""
    events = [_event("chatbot", [FakeMsg(content="", tool_calls=[{"name": "x", "args": {}}])])]
    assert extract_final_text(events) == ""


def test_extract_final_text_ignores_non_string_content() -> None:
    """content 不是 str 時應該忽略 (避免拿到 list[dict] 之類的東西)。"""

    @dataclass
    class WeirdMsg:
        content: list[dict[str, Any]]

    events: list[dict[str, Any]] = [
        {"chatbot": {"messages": [WeirdMsg(content=[{"type": "text", "text": "嗨"}])]}},
        _event("chatbot", [FakeMsg(content="正常字串")]),
    ]
    assert extract_final_text(events) == "正常字串"
