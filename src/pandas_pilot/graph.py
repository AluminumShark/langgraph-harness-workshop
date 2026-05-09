"""組裝 Data Analyst Agent 的 graph。"""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .tools import inspect_data, run_pandas

DEFAULT_SYSTEM_PROMPT = """你是一位嚴謹的資料分析助理。

工作流程鐵則:
1. 拿到任何問題後,先呼叫 inspect_data 看資料的 shape、欄位、缺失值。
2. 看完 inspect_data 才能呼叫 run_pandas 做分析。
3. 處理完所有缺失值再回報結果。
4. 用繁體中文回覆,先給結論再附上關鍵數字。
"""


def build_graph(system_prompt: str | None = None):
    """建立 ReAct agent graph。

    參數:
        system_prompt: 可選的 system prompt。傳 None 跑 baseline 版本(無 system prompt)
    回傳:
        compiled graph
    """
    tools = [inspect_data, run_pandas]
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: MessagesState) -> dict:
        messages = state["messages"]
        # 沒給就走 baseline;有給就確保 system prompt 永遠在 messages 最前面
        if system_prompt is not None and (
            not messages or not isinstance(messages[0], SystemMessage)
        ):
            messages = [SystemMessage(content=system_prompt), *messages]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", tools_condition)
    builder.add_edge("tools", "chatbot")

    return builder.compile()
