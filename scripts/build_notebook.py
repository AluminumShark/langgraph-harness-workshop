"""產生 notebooks/workshop.ipynb。

用 nbformat 組 cell,而不是手寫 JSON,避免不該手碰的格式錯誤。
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

OUT_PATH = Path(__file__).resolve().parent.parent / "notebooks" / "workshop.ipynb"


def md(text: str) -> nbf.notebooknode.NotebookNode:
    return nbf.v4.new_markdown_cell(text)


def code(text: str) -> nbf.notebooknode.NotebookNode:
    return nbf.v4.new_code_cell(text)


def build() -> nbf.NotebookNode:
    cells: list[nbf.notebooknode.NotebookNode] = []

    # === §0. 開場 ===
    cells.append(
        md("""# pandas-pilot · LangGraph 工作坊

> 從零打造一個會分析 CSV 的 ReAct agent,並學會用 trace + eval 把它當工程系統管。

## §0. 開場

今天結束你會看到這個對話:

```
USER: 幫我分析 data/sales.csv,哪個 region 平均 revenue 最低?
AGENT:
  → 呼叫 inspect_data("data/sales.csv")
  ← 回傳 shape、欄位、缺失值、前五筆
  → 呼叫 run_pandas("data/sales.csv", "df.dropna(subset=['region','revenue']).groupby('region')['revenue'].mean()")
  ← 回傳 East/West/North/South 的平均 revenue
AGENT: 平均 revenue 最低的 region 是 South,平均 ~XXX。已扣除 region/revenue 的缺失值。
```

跟著講師往下跑就對了——**不要只看 cell,要打開回傳物件看裡面**,這比聽講還重要。
""")
    )

    # === §1. 環境救火 ===
    cells.append(
        md("""## §1. 環境救火

### 拿 Google AI API key

1. 到 https://aistudio.google.com/apikey 拿一把免費的 Gemini API key
2. 複製 key,貼到下面那個 cell 的引號裡

> ⚠️ **這只是工作坊圖快**。實際開發請改用環境變數或 Colab secret,**不要把 API key commit 進 repo**。
""")
    )

    cells.append(md("先確保套件齊全(Colab 第一次跑要等一下)。"))
    cells.append(code("%pip install -q -U langgraph langchain langchain-google-genai pandas"))

    cells.append(
        md(
            "把剛才拿到的 API key **整段**貼到下面引號裡(連 placeholder 一起取代,"
            "不要前後留中文)。Google API key 長 39 字、以 `AIza` 開頭。"
        )
    )
    cells.append(
        code("""import os

# 工作坊圖快才這樣寫,正式專案不要這樣做
GOOGLE_API_KEY = "PASTE_YOUR_KEY_HERE"

# 安全檢查:沒貼 / 貼錯 / 不小心連中文一起貼,在這邊就擋掉
assert GOOGLE_API_KEY != "PASTE_YOUR_KEY_HERE", "請先把 key 貼進來"
assert GOOGLE_API_KEY.isascii(), "key 裡有非 ASCII 字元,你大概不小心把中文 placeholder 留下來了"
assert GOOGLE_API_KEY.startswith("AIza"), "Google API key 應該以 AIza 開頭,確認一下你貼對了"

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
print("API key 長度:", len(GOOGLE_API_KEY))
""")
    )

    cells.append(
        code("""from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
result = llm.invoke("用一句話說明你是誰")
print(result.content)
""")
    )

    # === §2. LangGraph 心智模型 ===
    cells.append(
        md("""## §2. LangGraph 心智模型

LangGraph 只有三個概念,記住就贏一半:

- **State**:一個 dict-like 物件,所有節點共享。把它想成「白板」。
- **Node**:一個 function,讀 State、回傳要更新的部分。
- **Edge**:節點之間的箭頭,決定下一個輪到誰跑。

整個 graph 跑起來就是:`State → Node A → 更新 State → Edge 決定下一個 → Node B → ...`

工作坊後半 agent 也只是這三件事的組合,不要覺得它神奇。
""")
    )

    # === §3. Python 速補 ===
    cells.append(
        md("""## §3. Python 速補

LangGraph 大量使用 type hint,先快速看過。
""")
    )

    cells.append(md("### §3.1 type hint"))
    cells.append(
        code("""# 變數
x: int = 20
name: str = "Alice"

# 函式參數與回傳
def add(a: int, b: int) -> int:
    return a + b

# Python runtime 不會檢查 hint(只是註解),靠 IDE / type checker
print(add(1, 2))
""")
    )

    cells.append(md("### §3.2 TypedDict — 結構化的 dict"))
    cells.append(
        code("""from typing import TypedDict


class User(TypedDict):
    name: str
    age: int


u: User = {"name": "Alice", "age": 30}
print(u)
print(type(u).__name__)  # 注意它本質還是 dict
""")
    )

    cells.append(md("### §3.3 Annotated — 給 type 加標籤"))
    cells.append(
        code("""from typing import Annotated

# Annotated[原本的型別, "說明 / 處理規則"]
Score = Annotated[int, "0-100 之間的整數"]

s: Score = 87
print(s)

# LangGraph 用 Annotated 來告訴 graph「這個欄位要怎麼合併」(後面會再用到)
""")
    )

    cells.append(md("### §3.4 `@tool` 裝飾器"))
    cells.append(
        code("""from langchain_core.tools import tool


@tool
def add_two(a: int, b: int) -> int:
    \"\"\"把兩個整數相加。\"\"\"
    return a + b


# tool 物件可以直接呼叫,但更重要的是它有 schema 給 LLM 看
print(add_two.invoke({"a": 3, "b": 4}))
print("---")
print(add_two.name)
print(add_two.description)
print(add_two.args)
""")
    )

    # === §4. 第一個 graph ===
    cells.append(
        md("""## §4. 第一個 graph: echo bot

最小可跑的 graph,只做一件事:把使用者訊息原封不動回傳。
""")
    )

    cells.append(
        code("""from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    text: str


def echo(state: State) -> dict:
    # 注意:回傳 dict,key 是要更新的 state 欄位
    return {"text": state["text"]}


builder = StateGraph(State)
builder.add_node("echo", echo)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)
graph = builder.compile()

result = graph.invoke({"text": "你好,LangGraph"})
print(result)
""")
    )

    cells.append(md("把 result 物件打開看一下。"))
    cells.append(
        code("""print(type(result).__name__)
print(repr(result))
print(result["text"])
""")
    )

    # === §5. 兩節點 + 邊 ===
    cells.append(
        md("""## §5. 兩節點 + 邊(clean → respond)

兩個節點接起來,前面 clean、後面 respond。學會節點之間怎麼接力。
""")
    )

    cells.append(
        code("""class State2(TypedDict):
    text: str


def clean(state: State2) -> dict:
    # 把訊息去頭去尾、轉小寫
    return {"text": state["text"].strip().lower()}


def respond(state: State2) -> dict:
    return {"text": f"我聽到你說: {state['text']}"}


b = StateGraph(State2)
b.add_node("clean", clean)
b.add_node("respond", respond)
b.add_edge(START, "clean")
b.add_edge("clean", "respond")
b.add_edge("respond", END)
g2 = b.compile()

print(g2.invoke({"text": "  HELLO World  "}))
""")
    )

    # === §6. LLM 物件解剖 ===
    cells.append(
        md("""## §6. LLM 物件解剖

接下來要把 LLM 接上 graph,先把 LLM 物件本身的回傳值看清楚。
""")
    )

    cells.append(md("### §6.1 llm.invoke"))
    cells.append(
        code("""resp = llm.invoke("用三個字回答:Python 是什麼?")
print(resp)
""")
    )

    cells.append(md("### §6.2 把 AIMessage 整個打開"))
    cells.append(
        code("""print("type:", type(resp).__name__)
print("content:", repr(resp.content))
print("tool_calls:", resp.tool_calls)
print("usage_metadata:", resp.usage_metadata)
print("response_metadata keys:", list(resp.response_metadata.keys()))
""")
    )

    cells.append(
        md("""注意 `resp.content` 在新版 Gemini(2.5+ 帶 reasoning)會回 **list of dict**,
裡面有 `type='text'` 跟 thought signature。要拿純文字字串,改用 `.text` property:
""")
    )
    cells.append(
        code("""# .content 是 raw,可能是 str 也可能是 list of dict
print("raw content:", repr(resp.content)[:200], "...")

# .text 是統一的純字串訪存
print("text:", resp.text)
""")
    )

    cells.append(
        md("""**經驗法則:展示給人看用 `.text`,做訊息序列化或要看完整結構用 `.content`。**
""")
    )

    cells.append(md("### §6.3 多輪對話:messages 是 list,LLM 沒記憶"))
    cells.append(
        code("""from langchain_core.messages import AIMessage, HumanMessage

# LLM 自己沒記憶,你必須把整段對話歷史塞給它
history = [
    HumanMessage(content="我叫 Alice"),
    AIMessage(content="你好 Alice!"),
    HumanMessage(content="我叫什麼?"),
]
print(llm.invoke(history).text)
""")
    )

    cells.append(
        code("""# 反例:不傳 history,只傳最後一句
print(llm.invoke("我叫什麼?").text)
""")
    )

    # === §7. MessagesState ===
    cells.append(
        md("""## §7. MessagesState

LangGraph 內建 `MessagesState`,專門處理「累積一個 message list」這個常見場景。
""")
    )

    cells.append(
        code("""from langgraph.graph import MessagesState


def chatbot(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"])
    # 注意:回傳一個 list,LangGraph 會自動 append 進去
    return {"messages": [response]}


b = StateGraph(MessagesState)
b.add_node("chatbot", chatbot)
b.add_edge(START, "chatbot")
b.add_edge("chatbot", END)
g3 = b.compile()

result = g3.invoke({"messages": [HumanMessage(content="嗨,我叫 Alice")]})
for m in result["messages"]:
    print(type(m).__name__, "-", m.content)
""")
    )

    cells.append(
        md("""### 反例:如果用普通 dict 取代 MessagesState

假如不用 MessagesState、自己用 list 又沒有設定 reducer,新訊息會**蓋掉**舊訊息,而不是 append。MessagesState 內部用 `Annotated[list, add_messages]`,告訴 graph「這個欄位要用 add_messages 合併」。
""")
    )

    # === §8. Tool Calling ===
    cells.append(
        md("""## §8. Tool Calling(前半場核心)

把 tool 接上 LLM,讓它能呼叫我們寫的函式。
""")
    )

    cells.append(md("### §8.1 bind_tools 後看 LLM 回什麼"))
    cells.append(
        code("""from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    \"\"\"查詢城市的天氣。\"\"\"
    return f"{city} 是晴天 25 度"


llm_with_tools = llm.bind_tools([get_weather])
resp = llm_with_tools.invoke("台北今天天氣怎樣?")
print("content:", repr(resp.content))
print("tool_calls:", resp.tool_calls)
""")
    )

    cells.append(
        md("""注意兩件事:

1. **content 是空字串**——LLM 決定先呼叫 tool,還沒生最終回答
2. **tool_calls 是一個 list of dict**,每個 dict 有 name / args / id

LLM 不會自動執行 tool,只是「指示要呼叫」。執行是你的事(後面的 ToolNode 會幫你)。
""")
    )

    cells.append(md("### §8.2 docstring 是 LLM 唯一的「使用說明書」"))
    cells.append(
        code("""# LLM 看不到你的程式碼,只看到 tool 的 name、docstring、參數
print(get_weather.name)
print(get_weather.description)  # 這就是 docstring
print(get_weather.args)
""")
    )

    cells.append(
        md("""**docstring 寫得爛 → tool 沒人用**。等下我們會寫一個 docstring 強制 LLM「先 inspect 才 run」的範例。
""")
    )

    cells.append(md("### §8.3 兩個 tool: inspect_data / run_pandas"))
    cells.append(
        code("""import io

import pandas as pd
from langchain_core.tools import tool


@tool
def inspect_data(path: str) -> str:
    \"\"\"檢查 CSV 資料品質。執行任何 groupby/filter/agg 之前**必須**先呼叫
    這個工具,了解資料的形狀、欄位、缺失值情況。

    參數:
        path: CSV 檔案路徑
    回傳:
        字串,包含 shape、欄位、缺失值、前五筆樣本
    \"\"\"
    df = pd.read_csv(path)
    buf = io.StringIO()
    buf.write(f"shape: {df.shape}\\n")
    buf.write(f"columns: {list(df.columns)}\\n")
    buf.write("\\ndtypes:\\n")
    buf.write(df.dtypes.to_string())
    buf.write("\\n\\nmissing values per column:\\n")
    buf.write(df.isna().sum().to_string())
    buf.write("\\n\\nhead(5):\\n")
    buf.write(df.head(5).to_string())
    return buf.getvalue()


@tool
def run_pandas(path: str, code: str) -> str:
    \"\"\"對 CSV 執行 pandas 分析程式碼,例如 groupby、filter、agg、sort 等。
    讀好的 DataFrame 以 `df` 變數提供,可直接在 code 中使用。

    參數:
        path: CSV 檔案路徑
        code: 一段 pandas expression(例如 "df.groupby('region')['revenue'].mean()")
    回傳:
        執行結果的字串(超過 2000 字會截斷)
    \"\"\"
    # ⚠️ 注意:eval() 在 production 是嚴重安全問題
    # 此處為了工作坊講解簡化,實務上請改 sandbox / RestrictedPython / e2b
    df = pd.read_csv(path)
    try:
        result = eval(code, {"df": df, "pd": pd})
    except Exception as exc:
        return f"執行錯誤:{type(exc).__name__}: {exc}"
    text = str(result)
    if len(text) > 2000:
        text = text[:2000] + "\\n... (output truncated)"
    return text


tools = [inspect_data, run_pandas]
print([t.name for t in tools])
""")
    )

    cells.append(
        md(
            "準備 demo 資料:`data/sales.csv` 不存在就現場生一份。"
            "故意混了 5 個 region NaN + 5 個 revenue NaN,讓 inspect_data 看得到。"
        )
    )
    cells.append(
        code("""import os
import random
from datetime import date, timedelta

CSV_PATH = "data/sales.csv"

if not os.path.exists(CSV_PATH):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    rng = random.Random(42)
    regions = ["East", "West", "North", "South"]
    products = ["Widget", "Gadget", "Gizmo", "Doohickey"]
    base = date(2025, 1, 1)
    rows = []
    for _ in range(100):
        region = rng.choice(regions)
        unit_price = rng.uniform(8, 18) if region == "South" else rng.uniform(20, 60)
        units = rng.randint(1, 50)
        rows.append({
            "date": (base + timedelta(days=rng.randint(0, 89))).isoformat(),
            "region": region,
            "product": rng.choice(products),
            "units": units,
            "revenue": round(units * unit_price, 2),
        })
    df = pd.DataFrame(rows)
    df.loc[rng.sample(range(100), 5), "region"] = pd.NA
    df.loc[rng.sample(range(100), 5), "revenue"] = pd.NA
    df.to_csv(CSV_PATH, index=False)
    print(f"已生成 {CSV_PATH}({len(df)} 筆)")
else:
    print(f"{CSV_PATH} 已存在")
""")
    )

    cells.append(md("先測試 tool 自己跑得起來。"))
    cells.append(
        code("""print(inspect_data.invoke({"path": CSV_PATH}))
""")
    )

    cells.append(md("### §8.4 組裝 graph: ToolNode + tools_condition"))
    cells.append(
        code("""from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: MessagesState) -> dict:
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
# tools_condition: 如果上一則訊息有 tool_calls,走 tools 節點;否則走 END
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")  # tools 跑完繞回 chatbot

agent = builder.compile()
print("agent compiled.")
""")
    )

    cells.append(md("### §8.5 試跑三次同樣問題"))
    cells.append(
        code("""question = f"幫我分析 {CSV_PATH},哪個 region 平均 revenue 最低?"

for i in range(3):
    print(f"========== 第 {i + 1} 次 ==========")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    # 用 .text 拿純字串(原因見 §6.2)
    print(result["messages"][-1].text)
    print()
""")
    )

    cells.append(
        md("""**這就是 stochastic 的本性**。三次答案不一致很正常,有時候它甚至不 inspect 就直接 run。後半場我們會用 trace + eval 把它管起來。
""")
    )

    cells.append(md("### §8.6 把 result['messages'] 整個打開"))
    cells.append(
        code("""result = agent.invoke({"messages": [{"role": "user", "content": question}]})

for i, m in enumerate(result["messages"]):
    print(f"--- [{i}] {type(m).__name__} ---")
    tc = getattr(m, "tool_calls", None)
    if tc:
        for call in tc:
            print(f"  tool_call -> {call['name']}({call['args']})")
    else:
        # .text 統一從 str / list-of-dict 兩種 content 形狀拿出純字串
        text = m.text if hasattr(m, "text") else str(m.content)
        if len(text) > 300:
            text = text[:300] + "..."
        print(f"  {text}")
""")
    )

    cells.append(
        md("""這就是 ReAct loop 的真實長相:

```
HumanMessage → AIMessage(tool_calls=[inspect_data]) → ToolMessage → AIMessage(tool_calls=[run_pandas]) → ToolMessage → AIMessage(最終回答)
```

每一輪 LLM 看到的都是「目前為止的所有訊息」,所以後面的 tool 結果它都看得到。
""")
    )

    # === §9. 前半場小結 ===
    cells.append(
        md("""## §9. 前半場小結

到這裡你已經:

- 看過 LangGraph 三件事:State / Node / Edge
- 寫過自己的 echo / clean+respond / chatbot
- 把 LLM 物件打開過,知道 content / tool_calls / usage_metadata 各是什麼
- 用 `bind_tools` + `ToolNode` + `tools_condition` 組出第一個會用工具的 agent
- **親眼看到同一個問題回三種答案**

但有兩個沒解決的問題:

1. **三次回不一樣**——怎麼知道哪一次「對」?
2. **改 prompt 不知道有沒有變好**——憑感覺嗎?

後半場處理這兩件事。
""")
    )

    # === §10. 後半場開場 ===
    cells.append(
        md("""## §10. 後半場開場 — Harness 是什麼

Harness = 把 agent 當「黑盒受測物」,在外面套一層工具,讓你能:

1. **觀察**它做了什麼(trace)
2. **打分數**它做得好不好(eval)
3. **回頭改**並再跑一次(loop)

接下來 §11 trace、§12 eval,§13 把它們組成 loop。
""")
    )

    # === §11. Trace ===
    cells.append(
        md("""## §11. Trace

`graph.invoke` 只給你最後結果,中間決策看不到。
換成 `graph.stream(..., stream_mode="updates")` 就能看到每一步。
""")
    )

    cells.append(
        code("""for event in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="updates",
):
    print(event)
    print("---")
""")
    )

    cells.append(md("raw event 太雜,寫一個 pretty_trace 把它列得人類看得懂。"))
    cells.append(
        code("""def pretty_trace(graph, user_message: str) -> list[dict]:
    events = []
    print(f"USER: {user_message}\\n")
    inputs = {"messages": [{"role": "user", "content": user_message}]}
    for step, event in enumerate(graph.stream(inputs, stream_mode="updates"), start=1):
        events.append(event)
        for node_name, node_state in event.items():
            print(f"--- step {step} | node: {node_name} ---")
            for msg in node_state.get("messages", []):
                role = type(msg).__name__
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    for call in tool_calls:
                        print(f"  [{role}] tool_call -> {call['name']}({call['args']})")
                else:
                    text = msg.text if hasattr(msg, "text") else str(msg.content)
                    if len(text) > 400:
                        text = text[:400] + "..."
                    print(f"  [{role}] {text}")
            print()
    return events


events = pretty_trace(agent, question)
""")
    )

    # === §12. Eval ===
    cells.append(
        md("""## §12. Eval

Trace 讓你「看得到」,eval 讓你「打分數」。我們先寫 5 個 case。
""")
    )

    cells.append(
        code("""EVAL_CASES = [
    {
        "id": "001_must_inspect_first",
        "user_message": f"幫我看一下 {CSV_PATH} 這份資料的概況。",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
    {
        "id": "002_handle_empty_result",
        "user_message": f"在 {CSV_PATH} 裡找出 region 是 'Mars' 的紀錄總數。",
        "must_call_first": "inspect_data",
        "must_contain_in_final": ["0"],
    },
    {
        "id": "003_inspect_before_summary",
        "user_message": f"幫我計算 {CSV_PATH} 的 revenue 平均。",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
    {
        "id": "004_top_region",
        "user_message": f"分析 {CSV_PATH},哪個 region 的平均 revenue 最低?",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
    {
        "id": "005_count_rows",
        "user_message": f"{CSV_PATH} 總共有幾筆資料?",
        "must_call_first": "inspect_data",
        "must_contain_in_final": [],
    },
]
print(f"共 {len(EVAL_CASES)} 個 case")
""")
    )

    cells.append(md("寫兩個 helper:抽 tool_calls 順序、抽最後一段文字。"))
    cells.append(
        code("""def extract_tool_calls(events):
    names = []
    for event in events:
        for _node, state in event.items():
            for msg in state.get("messages", []) or []:
                for call in getattr(msg, "tool_calls", None) or []:
                    names.append(call["name"])
    return names


def extract_final_text(events):
    final = ""
    for event in events:
        for node, state in event.items():
            if node != "chatbot":
                continue
            for msg in state.get("messages", []) or []:
                if not getattr(msg, "tool_calls", None):
                    final = msg.text if hasattr(msg, "text") else str(getattr(msg, "content", "") or "")
    return final
""")
    )

    cells.append(
        code("""def evaluate_one(graph, case):
    inputs = {"messages": [{"role": "user", "content": case["user_message"]}]}
    events = list(graph.stream(inputs, stream_mode="updates"))
    tc = extract_tool_calls(events)
    final = extract_final_text(events)

    reasons = []
    if case["must_call_first"]:
        if not tc:
            reasons.append(f"沒呼叫任何 tool(預期 {case['must_call_first']})")
        elif tc[0] != case["must_call_first"]:
            reasons.append(f"第一個 tool 是 {tc[0]},預期 {case['must_call_first']}")
    for kw in case.get("must_contain_in_final", []):
        if kw not in final:
            reasons.append(f"最終回覆缺關鍵字 {kw!r}")

    return {"id": case["id"], "passed": not reasons, "reasons": reasons,
            "tool_calls": tc, "final_text": final}


def run_eval_suite(graph, cases):
    results = []
    for c in cases:
        r = evaluate_one(graph, c)
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"[{mark}] {r['id']}  tool_calls={r['tool_calls']}")
        for reason in r["reasons"]:
            print(f"        - {reason}")
        results.append(r)
    p = sum(1 for r in results if r["passed"])
    print(f"\\n通過 {p}/{len(results)} ({p / len(results):.0%})")
    return results
""")
    )

    cells.append(md("### baseline:沒 system prompt 的 agent"))
    cells.append(
        code("""baseline_results = run_eval_suite(agent, EVAL_CASES)
""")
    )

    cells.append(
        md("""通常會看到 **40-60% pass**——agent 常常省略 inspect、直接 run_pandas。

接下來加 system prompt 重跑。
""")
    )

    cells.append(md("### v2:加 system prompt"))
    cells.append(
        code("""from langchain_core.messages import SystemMessage

SYSTEM_PROMPT = \"\"\"你是一位嚴謹的資料分析助理。

工作流程鐵則:
1. 拿到任何問題後,先呼叫 inspect_data 看資料的 shape、欄位、缺失值。
2. 看完 inspect_data 才能呼叫 run_pandas 做分析。
3. 處理完所有缺失值再回報結果。
4. 用繁體中文回覆,先給結論再附上關鍵數字。
\"\"\"


def chatbot_v2(state: MessagesState) -> dict:
    msgs = state["messages"]
    if not msgs or not isinstance(msgs[0], SystemMessage):
        msgs = [SystemMessage(content=SYSTEM_PROMPT), *msgs]
    return {"messages": [llm_with_tools.invoke(msgs)]}


b2 = StateGraph(MessagesState)
b2.add_node("chatbot", chatbot_v2)
b2.add_node("tools", ToolNode(tools))
b2.add_edge(START, "chatbot")
b2.add_conditional_edges("chatbot", tools_condition)
b2.add_edge("tools", "chatbot")
agent_v2 = b2.compile()

v2_results = run_eval_suite(agent_v2, EVAL_CASES)
""")
    )

    cells.append(
        md("""預期 **80-100% pass**。

關鍵點:**你現在有了客觀數字**,可以說「v2 比 baseline 好」、「再改 prompt 看分數變化」、「跑 CI 卡 regression」——agent 從藝術變工程。
""")
    )

    # === §13. Harness Loop ===
    cells.append(
        md("""## §13. Harness Loop 概念

把 trace + eval 串起來,你就有一個 dev loop:

```
1. 改 agent(prompt / tool / graph)
2. run_eval_suite(agent)
3. 看哪個 case 跌了 → pretty_trace(agent, that_case) → 看出問題
4. 回 1
```

**這個 loop 才是 agent 工程化的核心**——不是 LangGraph、不是 Gemini。任何框架、任何 LLM,只要能跑這個 loop,就能維護。

進階:把 eval 跑進 CI、加 coverage matrix(case x model x prompt)、加 cost / latency 指標——但都是這個 loop 的延伸。
""")
    )

    # === §14. 收場 ===
    cells.append(
        md("""## §14. 收場 + 課後練習

今天你學到:

- LangGraph: State / Node / Edge / MessagesState / ToolNode / tools_condition
- Tool calling 的真實長相(ReAct loop)
- 為什麼 agent 是 stochastic、為什麼 docstring 重要
- 用 trace 看中間步驟、用 eval 打客觀分數
- harness loop 是 agent 工程化的基礎

### 課後練習

1. **加新 case**:讓 baseline 通過,但 v2 反而失敗——觀察 prompt over-fit
2. **第三個 tool**:加 `plot_data(path, code)` 產 base64 PNG,並寫 case 驗證它沒被誤用
3. **跨模型比較**:把 `gemini-2.5-flash` 換成 `gemini-2.5-pro`,跑同一份 EVAL_CASES,看分數差距
4. **改 trace**:把 latency / token usage 加進 pretty_trace,你就能看到每個 case 的 cost
5. **CI 化**:把 EVAL_CASES 寫進 pytest,在 GitHub Actions 跑 nightly

歡迎發 PR / issue:https://github.com/AluminumShark/langgraph-harness-workshop
""")
    )

    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.11",
        },
    }
    return nb


def main() -> None:
    nb = build()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"已寫入 {OUT_PATH}({len(nb['cells'])} cells)")


if __name__ == "__main__":
    main()
