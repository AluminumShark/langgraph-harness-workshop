# LangGraph 工作坊：兩小時打造你的第一個 Data Analyst Agent

> **台大 AI 社・2 小時實作工作坊**
> **講師教案 + 學員 Notebook**
>
> **受眾**：只會基礎 Python（會寫 function、用 list/dict，看過 class 但不熟；**沒寫過裝飾器、沒呼叫過 LLM API、沒用過 LangChain、沒寫過 async**）
> **產出**：每位學員寫出一個會自主探索 CSV 的 agent，並親身體驗為什麼需要 harness
> **配套**：[langgraph-workshop.ipynb](langgraph-workshop.ipynb)（Colab 直接開）

---

## ⚠️ 給講師：學員真實程度校準

**他們會的**：if/for/while、function、list/dict 操作、`pd.read_csv`、看得懂簡單的 type hint

**他們不會的**：
- 寫 class（看得懂繼承但不會寫）
- 裝飾器（看過 `@something` 但不知道機制）
- TypedDict / Annotated / typing_extensions
- 任何 LLM API 呼叫（沒看過 `llm.invoke` 回什麼物件）
- async / await
- 巢狀 for/if 寫起來不流暢
- LangChain 是什麼

**因此這份教案的紀律**：

1. **每一個新概念用之前都有「30 秒定義盒」**——不假設學過
2. **物件內容都打開來 print 給學員看**——不黑箱
3. **後半場 helper function 預先寫好在 Notebook**——學員看怎麼用，不看怎麼實作
4. **明確區分「動手敲」vs「看講師 demo」時段**——不要每行都讓學員自己敲
5. **前半場最後主動告訴學員「等下你的 agent 行為可能跟旁邊不一樣，這是正常的」**——保留 productive failure，移除自我懷疑成本

---

## 教學弧線

```
前半場（0:00–1:35）：寫出第一個 agent
  └─ 不講工程實踐，只教 LangGraph 三件事：State、Node、Tool
  └─ 故意不設 system prompt，行為不穩定（為後半場埋伏筆）

中場（1:35–1:40）：休息

後半場（1:40–2:55）：把 agent 升級成可工程化的東西
  └─ 用「四階段演進」敘事重新定位前半場
  └─ 教 trace（看見 agent 的決策）
  └─ 教 eval（量化 agent 的行為）
  └─ 講框架選型 + 收場
  └─ Replay 整節砍掉（對初學者太奢侈，留作課後）
```

---

# 前半場：寫出你的第一個 Agent

## 0. 開場 5 分鐘：今天要做出什麼

直接展示**最終 demo**：

```
你：分析 sales.csv，找出表現最差的區域
agent：[呼叫 inspect_data] [呼叫 run_pandas]
       → 是 East 區域，營收 $X，比平均低 30%
你：那 West 區呢？
agent：[記得剛才的 csv，繼續分析]
       → West 區營收 $Y，是表現最好的
```

「兩小時後你會自己寫出這個。場景是 **Data Analyst Agent**——丟它一份 CSV，它會自己決定要先檢查資料、再 groupby、最後寫出結論。」

**為什麼選這個場景**：你們之後寫 paper、做研究都會跑資料分析。

---

## 1. 環境救火（10 分鐘）

打開 Google Colab → 新建 notebook → 第一格：

```bash
!pip install -U langgraph langchain langchain-anthropic pandas
```

API key 設定（Colab 左側鑰匙圖示 → Secrets）：
- 名稱：`ANTHROPIC_API_KEY`
- 值：講師現場發放

驗證：

```python
import os
from google.colab import userdata
os.environ["ANTHROPIC_API_KEY"] = userdata.get("ANTHROPIC_API_KEY")

from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
print(llm.invoke("say hi in 5 words").content)
```

跑得出回覆 = 就緒。

> **講師救命繩**：準備一個「已能跑」的 Colab 公開連結。任何人卡 5 分鐘以上直接 fork 過去，不要拖全班。CSV（一份**故意有 NaN、有重複 row 的 sales.csv**）也預先放在公開連結。

---

## 2. 心智模型：什麼是 LangGraph（5 分鐘）

只講一句話：**LangGraph 把 AI 流程畫成一張圖**。

- **節點（Node）**：一個步驟（例如「檢查資料」「呼叫 LLM」）
- **邊（Edge）**：步驟之間的流向
- **狀態（State）**：節點之間傳遞的資料包

```
START → load_csv → analyze → END
```

這就是 LangGraph 的全部。

---

## 3. Python 速補：兩個你必須先看過的東西（5 分鐘）

> **講師說明**：這節是新增的，不能省。原本教案直接寫 `class State(TypedDict)` 就上 echo bot——對沒寫過 class、沒看過 TypedDict 的學員，這行有兩個障礙。先補完再進 §4。

### 3.1 TypedDict 是什麼

**一句話**：TypedDict 是一個**長得像 class 的 dict 設計圖**——告訴別人「這個 dict 應該有哪些 key、各是什麼型別」。

```python
from typing_extensions import TypedDict

# 設計圖：一個 User dict 應該有 name 和 age
class User(TypedDict):
    name: str
    age: int

# 實際使用就是普通的 dict
alice: User = {"name": "Alice", "age": 20}
print(alice["name"])  # "Alice"
```

**重點三件事**：
1. **它就是 dict**——不是真的 class，沒有 `self`、沒有 method，存取用 `alice["name"]` 不是 `alice.name`
2. **typing_extensions 是 typing 的「進階版」**——某些新功能 typing 還沒有，要從 typing_extensions 拿。記住寫法即可
3. **零 runtime 開銷**——只是給編輯器跟 LangGraph 看的提示，跑起來跟普通 dict 完全一樣

> 「為什麼不用 dataclass / Pydantic？因為 LangGraph 規定 State 用 TypedDict。其他你可能聽過的工具今天不討論。」

### 3.2 `Annotated` 是什麼（先預告，等到 §7 才會用到）

```python
from typing_extensions import Annotated

x: Annotated[int, "這是一個年齡"]  # 把 int 加上一個註解
```

**一句話**：Annotated 讓你給型別**夾帶額外資訊**。Python 本身不會用這資訊，但**框架（例如 LangGraph）可以讀**。

「等下 §7 你會看到 `Annotated[list, add_messages]`——意思是『這是 list，但 LangGraph 請用 add_messages 這個函數來合併它』。**現在不懂沒關係，看到再講。**」

---

## 4. 第一個 Graph：echo bot（15 分鐘）

最小可跑的 graph。**只教 State / Node / compile / invoke 四件事，不教 tool、不教 routing**。

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. 定義 State：節點之間傳什麼資料
class State(TypedDict):
    user_input: str
    response: str

# 2. 定義 Node：function 簽名一定是 state -> dict
def echo(state: State) -> dict:
    return {"response": f"你說的是：{state['user_input']}"}

# 3. 組裝 graph
builder = StateGraph(State)
builder.add_node("echo", echo)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

# 4. compile 後才能 invoke
graph = builder.compile()

# 5. 跑
result = graph.invoke({"user_input": "你好"})
print(result)
# {'user_input': '你好', 'response': '你說的是：你好'}
```

逐段講：

### 4.1 State 定義

剛剛 §3 教過 TypedDict——這是「設計圖」，告訴 LangGraph 我們的 state 有 `user_input` 跟 `response` 兩個欄位。

### 4.2 Node 是 `state -> dict`

```python
def echo(state: State) -> dict:
    return {"response": f"你說的是：{state['user_input']}"}
```

每個節點是一個 **function**——吃 state（dict）、return 一個 dict。

**關鍵概念：「return 的 dict 會被自動 merge 進 state」是什麼意思？**

```python
# 進 echo 之前，state 是：
{"user_input": "你好", "response": ""}

# echo return 的：
{"response": "你說的是：你好"}

# LangGraph 把它「merge」進去（用 dict.update 那種感覺）：
{"user_input": "你好", "response": "你說的是：你好"}
#  ↑ 沒被改                      ↑ 被更新
```

**所以你只 return 你要更新的欄位就好**——不用每次把整個 state 抄一遍。

### 4.3 組裝 graph

```python
builder = StateGraph(State)        # 開一張白紙，告訴它 State 長怎樣
builder.add_node("echo", echo)     # 加一個叫 "echo" 的節點，內容是 echo function
builder.add_edge(START, "echo")    # 從 START 走到 echo
builder.add_edge("echo", END)      # echo 走到 END
```

`START` 和 `END` 是 LangGraph 內建的「起點」和「終點」標記，從 `langgraph.graph` import。

### 4.4 compile() 是必須的

```python
graph = builder.compile()
```

`compile()` 把這張圖變成「可以跑的東西」，順便檢查圖合不合法（節點都連到了嗎？）。

> **第一個會踩的雷**：直接寫 `builder.invoke()` ❌——失敗。一定要先 compile。

### 4.5 invoke 餵進初始 state

```python
result = graph.invoke({"user_input": "你好"})
print(result)
```

回傳是**完整的 final state**。

### 4.6 動手時間（5 分鐘）

> **講師明示**：「這節最後 5 分鐘大家自己動手——把 echo 改成『把使用者輸入轉成大寫』。寫完跑出來舉手，我巡一圈確認大家都跑得出來。」

---

## 5. 第二個 Graph：兩個節點 + 邊（10 分鐘）

```python
class State(TypedDict):
    user_input: str
    cleaned: str
    response: str

def clean(state: State) -> dict:
    return {"cleaned": state["user_input"].strip().lower()}

def respond(state: State) -> dict:
    return {"response": f"處理後：{state['cleaned']}"}

builder = StateGraph(State)
builder.add_node("clean", clean)
builder.add_node("respond", respond)
builder.add_edge(START, "clean")
builder.add_edge("clean", "respond")
builder.add_edge("respond", END)

graph = builder.compile()
result = graph.invoke({"user_input": "  HELLO  "})
print(result)
# {'user_input': '  HELLO  ', 'cleaned': 'hello', 'response': '處理後：hello'}
```

**重點（用「水管」比喻）**：
- 兩個節點之間**完全不直接互相呼叫**——只透過 state 溝通
- `clean` 把處理結果寫進 state 的 `cleaned` 欄位，`respond` 從 state 讀 `cleaned`
- **state 是節點之間唯一的水管**

> **不動手**——這節跟 §4 結構幾乎一樣，講師演示就好，**節省學員的認知能量留給後面**。

---

## 6. LLM 物件解剖：先打開黑箱再進 agent（10 分鐘）

> **講師說明**：這節是新增的關鍵節。原本教案直接寫 `state["messages"]` 跟 `llm.invoke`，但學員從沒看過 LLM API 回什麼。先花 10 分鐘把這個黑箱打開，後面 §7 §8 會輕鬆很多。

### 6.1 LLM 怎麼呼叫

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

response = llm.invoke([
    {"role": "user", "content": "你好"}
])

print(type(response))
# <class 'langchain_core.messages.ai.AIMessage'>

print(response.content)
# '你好！有什麼我可以幫你的嗎？'
```

**重點解剖**：

1. **`llm.invoke(messages)`** 吃一個 **list of dicts**，每個 dict 有 `role`（誰說的）和 `content`（說了什麼）。`role` 可以是 `"user"`、`"assistant"`、`"system"`
2. **回傳是一個 `AIMessage` 物件**——不是字串！要拿文字內容用 `.content`
3. **Message 物件還有其他屬性**——例如 `.tool_calls`（等下會看到）、`.id` 等。現在只要知道 `.content` 就夠了

### 6.2 多輪對話：messages 是 list

```python
response = llm.invoke([
    {"role": "user", "content": "我叫小明"},
    {"role": "assistant", "content": "你好，小明！"},
    {"role": "user", "content": "我叫什麼名字？"}
])
print(response.content)
# '你叫小明。'
```

**LLM 沒有記憶**——你每次 invoke 要把整段歷史傳進去，它才知道剛才聊過什麼。

> 這個事實對後面理解 MessagesState 至關重要：為什麼 LangGraph 要把 messages 包成 list、為什麼要 append 不要覆蓋？因為 LLM 需要看完整歷史。

### 6.3 LLM 是黑盒，但**它的 input/output 是 dict 跟物件**——你看得見

「LLM 內部怎麼決策我們不討論。但**送進去什麼、拿出來什麼**——這些是 Python 物件，可以 print、可以 inspect。**有不確定的時候 print 出來看，是 debug LLM 程式碼最重要的習慣。**」

---

## 7. MessagesState：對話 agent 的標準寫法（10 分鐘）

```python
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def chatbot(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

graph = builder.compile()
result = graph.invoke({
    "messages": [{"role": "user", "content": "幫我寫一句 Python hello world"}]
})
print(result["messages"][-1].content)
```

**這是學員第一次看到 LLM 出現在 graph 裡。** 三個重點，慢慢講：

### 7.1 MessagesState 是什麼

LangGraph 內建的 State，內容大概是：

```python
class MessagesState(TypedDict):
    messages: Annotated[list, add_messages]
```

**現在 §3.2 預告的 `Annotated` 派上用場了**——這個寫法的意思是：

> 「這欄位是個 list，但 LangGraph 處理它的時候**不要覆蓋**，要用 `add_messages` 這個函數來合併（也就是 append）。」

### 7.2 為什麼 messages 要 append 不能覆蓋——現場 demo

> **講師動手 demo（學員看就好）**：
>
> 「我直接給大家看不用 `add_messages` 會發生什麼。」

```python
# 反例：自己寫的 State，沒用 add_messages
from typing_extensions import TypedDict

class BadState(TypedDict):
    messages: list   # 預設行為是「覆蓋」

def chatbot(state: BadState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(BadState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
bad_graph = builder.compile()

# 跑兩輪
r1 = bad_graph.invoke({"messages": [{"role": "user", "content": "我叫小明"}]})
print("第一輪 messages 數量：", len(r1["messages"]))
# 第一輪 messages 數量： 1   ← 怪怪的，輸入應該還在啊

# 把第一輪結果接著問第二題
r2 = bad_graph.invoke({"messages": r1["messages"] + [{"role": "user", "content": "我叫什麼名字？"}]})
print(r2["messages"][-1].content)
# 「我不知道你的名字...」  ← 第一輪訊息消失了
```

**看到 bug 比聽抽象解釋有效十倍。** Bug 的原因：`return {"messages": [response]}` 把整個 messages list **覆蓋**成只有 response 那一個。原本的 user message 不見了。

**正確版**就是 §7 上面的 `MessagesState`——`add_messages` 會幫我們 append 而不是覆蓋。

### 7.3 永遠 return 新 list，不要 append

```python
# ❌ 錯
def bad_node(state):
    state["messages"].append(new_msg)
    return state

# ✅ 對
def good_node(state):
    return {"messages": [new_msg]}
```

「**永遠不要直接 mutate state**」——讓 LangGraph 的 reducer（也就是 `add_messages`）幫你處理 merge。

---

## 8. Tool Calling：讓 agent 能呼叫工具（25 分鐘——前半場核心）

到這裡學員會寫對話 bot 了。但 bot 不是 agent——**agent 會自己決定要呼叫工具**。

### 8.1 概念：什麼是 Tool？什麼是 ReAct loop？

**Tool** = 你給 LLM 用的「工具」，本質是一個 Python function。

**LLM 怎麼決定呼叫 tool？這是學員最該理解的機制**：

1. 你把 tool 的「使用說明書」（function 名稱 + 參數 + docstring）打包成 schema，**透過 API 一起傳給 LLM**
2. LLM 看到使用者的問題，**決定要不要用 tool**：
   - 不用 → 直接回文字
   - 要用 → 回傳一個**特殊格式的訊息**，內容是「請呼叫 `inspect_data('sales.csv')`」
3. 你的程式（不是 LLM！）**讀到這個特殊訊息，去執行對應的 function**
4. 把執行結果**再餵回給 LLM**，讓它繼續思考

> 「**LLM 自己不會執行 Python 程式碼**——它只是『建議』要呼叫哪個 function。實際執行的人是你（或 LangGraph 的 ToolNode）。這個觀念極端重要。」

**ReAct loop**：

```
使用者問問題 → LLM 思考 → 要不要呼叫 tool？
                            ├─ 不要 → 直接回答 → END
                            └─ 要 → 呼叫 tool → 看到結果 → 再回去 LLM 思考
```

LLM 自己決定要不要呼叫工具、呼叫哪個、看到結果後要不要再呼叫——**這個 loop 就是 agent 的核心**。

### 8.2 實際看 LLM 怎麼回 tool_call（在進 LangGraph 之前先 demo）

> **這節是新增的關鍵 demo**——讓學員親眼看到「LLM 回的 tool_call 物件長什麼樣」，後面看 ToolNode 自動處理時才不黑箱。

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """查詢城市的天氣。輸入城市名，回傳天氣描述。"""
    return f"{city} 今天晴天，25 度"

# 把 tool 綁到 LLM 上
llm_with_tools = llm.bind_tools([get_weather])

response = llm_with_tools.invoke([
    {"role": "user", "content": "台北天氣怎樣？"}
])

print(response.content)
# ''   ← 注意是空字串！LLM 不打算用文字回答

print(response.tool_calls)
# [{'name': 'get_weather', 'args': {'city': '台北'}, 'id': 'toolu_01abc...'}]
# ↑ LLM「建議」我們去呼叫 get_weather('台北')
```

**重點解剖**：
- LLM 決定用 tool 時，`response.content` 通常是**空的**
- `response.tool_calls` 是一個 list，每個元素是 dict：`{"name": tool 名字, "args": 參數, "id": 識別碼}`
- **LLM 沒有真的執行 `get_weather`！** 它只是建議我們去呼叫
- 我們要拿這個 dict 去**自己呼叫**對應的 Python function

「OK，這就是『LLM 怎麼決定呼叫 tool』的全貌。沒有魔法。LangGraph 的 `ToolNode` 等下會幫我們做『讀 tool_calls → 呼叫 function → 把結果包回去』這一連串 boilerplate。」

### 8.3 `@tool` 裝飾器：30 秒定義盒

```python
@tool
def get_weather(city: str) -> str:
    """docstring 很重要！"""
    return f"..."
```

**裝飾器是什麼**：`@tool` 是把 function「包裝」一層的語法。原本 `get_weather` 只是普通 function，加了 `@tool` 之後它變成一個 LangChain 的 Tool 物件，多了「告訴 LLM 我長怎樣」的能力。

**docstring 為什麼重要**：LLM **完全靠 docstring 決定要不要呼叫這個 tool**。docstring 寫不清楚 = LLM 永遠不呼叫。好的 docstring 要交代：
- 做什麼
- 什麼時候該呼叫
- 參數意義
- 回傳什麼

### 8.4 完整實作 Data Analyst Agent

```python
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, MessagesState
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
import pandas as pd

@tool
def inspect_data(path: str) -> str:
    """檢查 CSV 資料品質：欄位、缺失值、樣本。"""
    df = pd.read_csv(path)
    return f"Shape: {df.shape}\nColumns: {list(df.columns)}\nMissing: {df.isna().sum().to_dict()}\nHead:\n{df.head().to_string()}"

@tool
def run_pandas(path: str, code: str) -> str:
    """執行 pandas 程式碼。code 內 df 變數已經是讀好的 DataFrame。"""
    df = pd.read_csv(path)
    safe_globals = {"df": df, "pd": pd}
    try:
        result = eval(code, safe_globals)
        return str(result)[:2000]
    except Exception as e:
        return f"Error: {e}"

tools = [inspect_data, run_pandas]
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929").bind_tools(tools)

def chatbot(state: MessagesState) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")
graph = builder.compile()
```

> **講師注意**：上面的 `chatbot` **故意沒有 system prompt**。後半場 productive failure 的關鍵伏筆——別自作主張幫學員加上去。

### 8.5 逐行解剖（這段慢慢講，這是新東西最多的一節）

| 元件 | 做什麼 | 給學員的話 |
|------|--------|----------|
| `@tool` | 把 function 變成 LLM 看得到的工具 | 「就是 §8.3 講的那個」 |
| `bind_tools(tools)` | 把工具的「說明書」附在每次 LLM 呼叫上 | 「§8.2 的 `llm_with_tools` 一樣的東西」 |
| `chatbot` 節點 | 呼叫 LLM，可能回文字、可能回 tool_calls | 「§8.2 看過 LLM 回的東西長怎樣」 |
| `ToolNode(tools)` | 內建節點——讀 tool_calls、執行 function、包結果 | 「§8.2 我們手動做的事情，LangGraph 自動做」 |
| `tools_condition` | 內建路由函數 | 「LLM 回的訊息有 `tool_calls` 就走 'tools'，沒有就走 END」 |
| `add_conditional_edges` | **新東西**——條件邊：依函數回傳值決定下一站 | 「跟 `add_edge` 不同，這個會看 state **動態決定**走哪」 |
| `add_edge("tools", "chatbot")` | 工具跑完回去 LLM | 「形成循環——LLM 看到結果決定下一步」 |

### 8.6 畫圖

```
START → chatbot ──tool_calls 是空─→ END
            │
            └─有 tool_calls─→ tools ─→ (回到 chatbot)
```

### 8.7 試跑 + 觀察

```python
result = graph.invoke({
    "messages": [{"role": "user", "content": "幫我分析 sales.csv，找出表現最差的區域"}]
})
print(result["messages"][-1].content)
```

讓學員自己跑跑看。

> **講師注意**：跑出來結果可能 East、可能 West、可能不一致。**講師看到不要解釋、不要修正、不要批判**——「對，agent 就是這樣，每次跑可能不太一樣」就好。

### 8.8 動手時間（10 分鐘）

> **講師明示**：「最後 10 分鐘自己跑——
> 1. 把上面的 graph 完整貼進 Colab
> 2. 跑一次「分析 sales.csv，找出表現最差的區域」
> 3. **重點任務**：把 `result["messages"]` print 出來看裡面有幾個 message、各是什麼 type、`.tool_calls` 有沒有東西
>
> 跑出來舉手，我巡一圈確認大家都跑得出來。」

**這個任務是刻意的**——強迫學員把 messages list 打開來看，內化「LangGraph 內部到底是怎麼跑的」。

---

## 9. 前半場小結 + 主動破除自我懷疑（5 分鐘）

> **這節是新增的，不能省**——保護學員心理安全感

「OK，前半場告一段落。我要先說一件**很重要**的事：

剛才大家跑出來的 agent，結果可能不太一樣——
- 有人跑出 East 是表現最差的
- 有人跑出 West
- 有人跑兩次答案不一樣

**這不是你寫錯了。** 這是 LLM agent 的**正常變異**——同一個程式、同一份資料，每次跑可能走不同路徑、做不同決定。

這是 LLM 的本質特性，**業界所有人都在處理這件事**。後半場我們就要學業界怎麼處理：怎麼**看見** agent 的決策（trace）、怎麼**量化** agent 的好壞（eval）。

休息 5 分鐘。」

---

# 中場休息（5 分鐘）

---

# 後半場：把 agent 變成可演進的工程

## 10. 後半場開場：四階段演進敘事（5 分鐘）

> **這 5 分鐘是整堂課的意識形態樞紐**——前半場學員寫的東西要在這裡被重新定位。

### 10.1 大家剛才都遇到了什麼

舉手調查（**真的舉手**）：
- 「剛剛 agent 跑出『最差是 East』的舉手」→ 一些人舉
- 「跑出『最差是 West』的舉手」→ 一些人舉
- 「兩次跑出來不一樣的舉手」→ 又一些人舉

「同一個程式、同一份資料、不同人跑出不同答案。這是 LLM agent 的本質。**問題是：你怎麼處理這件事？**」

### 10.2 業界四階段演進

```
2022──────2023──────2024──────2025──────2026──→
prompt    context   workflow  harness
engineer  engineer  engineer  engineer
```

| 階段 | 核心問題 | 代表性實踐 | 為什麼不夠 |
|------|---------|-----------|-----------|
| **Prompt engineering**<br>（2022–2023） | 「怎麼問 LLM 才聽話」 | few-shot、CoT、role prompting | 單輪、無狀態、無工具 |
| **Context engineering**<br>（2023–2024） | 「怎麼把對的資訊塞進 context」 | RAG、長 context、memory | 仍是「一次問答」，無流程 |
| **Workflow engineering**<br>（2024–2025） | 「怎麼把多步流程結構化」 | LangGraph、DAG agent、multi-agent | 跑得起來但**無法演進、無法量化** |
| **Harness engineering**<br>（2025– ） | 「怎麼讓 agent 可被工程化迭代」 | eval set、trace、replay、observability | ← **今天的位置** |

**你們前半場寫的是 workflow engineering 的標準作品**——LangGraph 是這個階段的代表工具。但業界已經知道這樣不夠了。

「不夠」的具體表現就是剛才舉手調查看到的：

| 問題 | 為什麼 workflow engineering 解不了 |
|------|---------------------------------|
| 兩次跑結果不一樣 | 沒有 **trace**，不知道差在哪一步 |
| 改一行 prompt 之後不知道變好變壞 | 沒有 **eval set**，沒有量化基準 |

### 10.3 Harness 是什麼

**Harness**（馬具）這個詞來自工程實踐：你給 LLM 套上一組「可控制、可觀測、可評估」的裝備，讓 agent 行為從**藝術品**變成**工業品**。

完整 harness 包含四件事：

| 元件 | 它讓你回答的問題 | 今天會教嗎 |
|------|---------------|-----------|
| **Trace** | 「這次 agent 為什麼這樣決策？」 | ✅ §11 |
| **Replay** | 「失敗時能不能從中間試？」 | ⏭ 課後練習（今天時間不夠） |
| **Eval** | 「我改了 prompt，整體變好還是變壞？」 | ✅ §12 |
| **Loop** | 「怎麼把上面接成持續改進的迴圈？」 | ✅ §13 |

「後半場我們把前半場寫的 agent 一步步包進這個 harness。」

---

## 11. Trace：讓 agent 的每一步可觀測（20 分鐘）

### 11.1 問題：剛才到底發生了什麼？

```python
result = graph.invoke({"messages": [...]})
print(result["messages"][-1].content)
```

學員只看得到最後一句答案。中間 agent 呼叫了哪些 tool、看到什麼結果——**全部不可見**。

### 11.2 解法：用 `stream` 取代 `invoke`

LangGraph 提供 `stream` 介面——跟 `invoke` 一樣的輸入，但會**把每個節點 return 的東西即時吐出來**：

```python
events = list(graph.stream(
    {"messages": [{"role": "user", "content": "分析 sales.csv，找出表現最差的區域"}]},
    stream_mode="updates",
))

# 先 print 出來看一下原始結構
print(events[0])
# 大概像：{'chatbot': {'messages': [AIMessage(content='', tool_calls=[...])]}}
```

「**`stream_mode="updates"` 的意思**：每個節點跑完後，把『它 return 了什麼』吐出來。`events` 是一個 list，每個元素是 `{節點名字: 那個節點 return 的 dict}`。」

> **講師動手 demo**：實際 print `events[0]`、`events[1]`...讓學員看到每個 event 的真實結構。**這個 5 分鐘比看著教案文字有用十倍。**

### 11.3 把 trace 包成漂亮的 print（這段 helper 已經寫在 Notebook 裡）

> **講師說明**：「這個 helper function 我已經寫在 Notebook 裡了，你不用敲。我快速講它在做什麼，重點是**會用**，不是會寫。」

```python
# Notebook 已預先寫好的 helper
def pretty_trace(graph, user_message: str):
    """跑 graph，把每個節點的決策漂亮印出來。"""
    inputs = {"messages": [{"role": "user", "content": user_message}]}
    for event in graph.stream(inputs, stream_mode="updates"):
        for node_name, update in event.items():
            print(f"\n[{node_name}]")
            for msg in update.get("messages", []):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  → 呼叫工具: {tc['name']}({tc['args']})")
                if hasattr(msg, "content") and msg.content:
                    print(f"  → 訊息: {msg.content[:150]}")
```

學員只需要呼叫：

```python
pretty_trace(graph, "分析 sales.csv，找出表現最差的區域")
```

學員會看到類似：

```
[chatbot]
  → 呼叫工具: inspect_data({'path': 'sales.csv'})

[tools]
  → 訊息: Shape: (100, 5)
         Columns: ['date', 'region', ...]
         Missing: {'region': 8, ...}

[chatbot]
  → 呼叫工具: run_pandas({'path': 'sales.csv', 'code': '...'})

[tools]
  → 訊息: region    revenue
         East      ...

[chatbot]
  → 訊息: East 區表現最差...
```

「**這就是 trace**。每個節點被觸發的順序、呼叫了什麼工具、看到什麼結果——全部看得見。」

### 11.4 回到舉手調查的問題

「**為什麼兩個人跑同樣的問題結果不一樣？**」

讓兩個學員把各自的 trace 印出來對比：
- A 同學：`[chatbot → inspect_data → chatbot → run_pandas → chatbot]` ✓
- B 同學：`[chatbot → run_pandas → chatbot]`（跳過 inspect）✗

「現在你知道差在哪了——B 同學的 LLM 決定不呼叫 `inspect_data`，所以沒看到 NaN，groupby 結果錯了。」

> **這就是 trace 的價值**：問題從「神祕」變成「具體可指認的步驟差異」。

### 11.5 動手時間（5 分鐘）

> **講師明示**：「自己用 `pretty_trace` 跑三次同樣的問題，看 agent 三次行為一不一樣。」

---

## 12. Eval：用數字說話（25 分鐘——後半場最重要）

### 12.1 問題：改了 prompt 之後不知道變好變壞

「假設我覺得剛才 agent 表現不夠好，我想加一句 system prompt：『記得先 inspect 再 groupby』。**改完之後我怎麼知道是真的變好了？**」

**慘痛事實**：很多人改 prompt 是靠「感覺好像比較好」。這就是為什麼 LLM 產品難以演進——你沒有客觀基準。

### 12.2 解法：寫 eval case

「**Eval case 就是『我認為 agent 應該怎麼做』的機械版本**——把標準寫成程式可以檢查的規則。」

```python
EVAL_CASES = [
    {
        "id": "001_must_inspect_first",
        "query": "找出表現最差的區域",
        "must_call_tools_in_order_prefix": ["inspect_data", "run_pandas"],
        # ↑ 第一個工具呼叫一定要是 inspect_data
        "answer_must_not_contain": ["NaN", "nan"],
        # ↑ 最終答案不能包含 NaN（代表沒處理乾淨）
        "answer_must_contain_one_of": ["East", "West", "North", "South"],
        # ↑ 答案要明確指出某個區域
    },
    {
        "id": "002_handle_empty_result",
        "query": "找出 2099 年的資料",
        "answer_must_contain_one_of": ["沒有", "找不到", "no data", "無資料"],
    },
]
```

「就是一個 list of dicts。每個 dict 描述一個檢查點。」

### 12.3 寫 eval runner（已經在 Notebook 裡）

> **講師說明**：「這個 runner 我也寫在 Notebook 裡了。**不用敲**——它的邏輯就是『跑 graph、抽出 tool 呼叫順序、抽出最終答案、檢查是否符合 case 描述的規則』。重點是會用。」

```python
# Notebook 已預先寫好的 eval runner
def evaluate_one(graph, case):
    events = list(graph.stream(
        {"messages": [{"role": "user", "content": case["query"]}]},
        stream_mode="updates",
    ))
    tool_seq = extract_tool_calls(events)
    answer = extract_final_text(events)

    checks = {}
    if "must_call_tools_in_order_prefix" in case:
        prefix = case["must_call_tools_in_order_prefix"]
        checks["tool_order"] = tool_seq[:len(prefix)] == prefix
    if "answer_must_not_contain" in case:
        checks["no_forbidden"] = all(
            kw.lower() not in answer.lower()
            for kw in case["answer_must_not_contain"]
        )
    if "answer_must_contain_one_of" in case:
        checks["has_required"] = any(
            kw.lower() in answer.lower()
            for kw in case["answer_must_contain_one_of"]
        )
    return {"case_id": case["id"], "passed": all(checks.values()), "checks": checks}

def run_eval_suite(graph, cases):
    results = [evaluate_one(graph, c) for c in cases]
    pass_rate = sum(r["passed"] for r in results) / len(results)
    return {"pass_rate": pass_rate, "results": results}
```

### 12.4 跑第一次 baseline

```python
report = run_eval_suite(graph, EVAL_CASES)
print(f"Pass rate: {report['pass_rate']:.0%}")
for r in report["results"]:
    status = "✓" if r["passed"] else "✗"
    print(f"  {status} {r['case_id']}: {r['checks']}")
```

**現場跑**——通常會看到 50–60% 左右（因為 agent 沒 system prompt，行為不穩定）。

### 12.5 加一行 prompt 看 eval 動（這節的高潮）

「現在我們**改一個地方**——加 system prompt：」

```python
SYSTEM_PROMPT = """你是資料分析助手。
在執行任何 groupby/filter/agg 操作之前，**必須**先呼叫 inspect_data 檢查資料品質。
如果有缺失值，先在答案中說明你怎麼處理。"""

def chatbot_v2(state: MessagesState) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(state["messages"])
    return {"messages": [llm.invoke(messages)]}

# 重新組 graph
builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot_v2)   # ← 換成新版
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")
graph_v2 = builder.compile()

# 重跑 eval
report_v2 = run_eval_suite(graph_v2, EVAL_CASES)
print(f"Pass rate: {report_v2['pass_rate']:.0%}")
```

**Pass rate 從 60% 變 90%**。

「**改一行 prompt，量化看到變好**——這就是工程化迭代的感覺。沒有 eval 你只能靠『感覺好像比較好』改 prompt。寫了 eval，你的迭代有方向、停損也有依據。」

### 12.6 Eval set 多大才算夠

學員必問。回答：

> 從 1 個開始就比 0 個好。每抓到一個失敗 case 就加一個。**有方向比有數量重要**。Anthropic 內部的 eval set 也是從幾十個 case 開始長到幾千個。今天你們寫了 2 個——已經比昨天的自己強了。

### 12.7 動手時間（10 分鐘）

> **講師明示**：「最後 10 分鐘——
> 1. 跑 baseline eval（沒 system prompt 那版）
> 2. 跑 v2 eval（有 system prompt 那版）
> 3. 看 pass rate 差多少
> 4. 自己想一個第三個 eval case 加進去（可以模仿前兩個的格式）」

---

## 13. Harness Loop：把全部串起來（5 分鐘）

```
        ┌─────────────────────────────┐
        │   LangGraph Agent           │
        │   (state + nodes + edges)   │
        └──────────────┬──────────────┘
                       │ invoke
                       ▼
              ┌─────────────────┐
              │ Trace + Checkpoint │  ← stream_mode="updates"
              │ (每步留下證據)        │
              └────────┬────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
      ┌──────────┐           ┌──────────┐
      │  Replay  │           │   Eval   │
      │ (課後玩)  │           │ (跑 cases) │
      └────┬─────┘           └────┬─────┘
           │                      │
           └──────────┬───────────┘
                      ▼
              ┌──────────────┐
              │  迭代 graph  │   ← 改 prompt / 改 tool / 改路由
              └──────┬───────┘
                     │
                     └──→ 回到頂部
```

「**今天兩小時你寫的東西已經涵蓋這整個迴圈的核心**。Replay 那塊我們留作課後練習——LangGraph 的 checkpointer 可以讓你『時光倒流』從任意 checkpoint 重跑，但今天時間不夠，留給你回家玩。」

---

## 14. 為什麼是 LangGraph：跟其他框架比起來如何（5 分鐘）

> **講師注意**：這段放在這裡是有刻意設計的——學員剛親身體驗過 trace、eval 是什麼感覺，這時候講「OpenAI Agents SDK 在這個工作流的代價是什麼」才有錨點。**體驗在前，比較在後**。

### 14.1 2026 年的 agent 框架格局（不是 LangGraph 獨大）

| 框架 | 推手 | 核心抽象 | 定位 |
|------|------|---------|------|
| **LangGraph** | LangChain | 顯式狀態圖 | 跨模型、production mileage 最高 |
| **OpenAI Agents SDK** | OpenAI | Handoff（agent 轉手） | 綁 OpenAI 模型，2026/4 剛加 harness 系統 |
| **Claude Agent SDK** | Anthropic | Tool-use chain + sub-agents | 從 Claude Code SDK 演變，綁 Claude 模型 |
| **CrewAI** | CrewAI Inc. | Role-based crews | 角色化多 agent，上手快 |
| **AWS Strands Agents** | AWS | Model-agnostic + Bedrock 整合 | AWS 生態系 |

**重點觀察**：harness 不是 LangGraph 獨家——OpenAI 在 2026 年 4 月剛追上加了 spans / resume / sandbox。但 LangGraph 在這個方向領先了一年多，工具鏈成熟度仍最高。

### 14.2 拿今天做過的事去比

| 你今天做了什麼 | LangGraph | 其他框架 |
|---|---|---|
| `stream_mode="updates"` 看 trace | ✅ 原生 | OpenAI 2026/4 才有；CrewAI 要靠第三方 |
| 寫 eval 量化行為 | ✅（搭 LangSmith 更完整） | 全市場都在補課 |
| 換 LLM 供應商一行改 | ✅ 跨模型 | OpenAI SDK 綁死 OpenAI；Claude SDK 綁死 Claude |
| Production mileage（Klarna/Uber/LinkedIn） | ✅ 最多 | 其他都比較新 |

### 14.3 LangGraph 也不是完美的

**誠實版劣勢**：
1. **學習曲線陡** —— 你們今天兩小時只摸了表面。OpenAI SDK 半小時能寫出第一個 agent
2. **寫起來囉嗦** —— 簡單任務 over-engineer
3. **API 變動快** —— 2024–2025 大改過，網路上 80% 中文教學是舊的

### 14.4 該怎麼選

| 你的場景 | 推薦 |
|---------|------|
| 第一次寫 agent / 一個工具 / 不用流程 | **OpenAI 直接 function calling** 三行寫完更好 |
| 已綁 OpenAI 生態系 + 簡單 handoff | **OpenAI Agents SDK** |
| **複雜流程 / 要 trace eval / 跨模型**（今天教的場景） | **LangGraph** |
| Anthropic 模型 + safety-critical | **Claude Agent SDK** |

**框架會變，但 harness 思維留下**——一年後你可能在用別的工具，但 trace、eval、迭代閉環會跟著你走。

---

## 15. Cheatsheet（5 分鐘）

### 15.1 LangGraph 必踩的 6 個雷

| # | 雷 | 正解 |
|---|-----|------|
| 1 | 直接 `state["messages"].append(...)` | 一律 `return {"messages": [new_msg]}`，讓 reducer 處理 |
| 2 | 自訂 State 沒寫 reducer，訊息列表被覆蓋 | `messages: Annotated[list, add_messages]` |
| 3 | 沒 `compile()` 就 `invoke` | `graph = builder.compile()` 後才能 invoke |
| 4 | `@tool` docstring 沒寫「使用時機」 | LLM 不知何時呼叫 → 永遠不呼叫 |
| 5 | 路由函數裡呼叫 LLM | 路由只讀 state 純值，LLM 放前一個節點 |
| 6 | 用舊 API（`MemorySaver`、`NodeInterrupt`） | 新 API：`InMemorySaver`、`interrupt()` |

### 15.2 Harness 自檢清單

寫 production agent 之前自問：

- [ ] **能 trace 嗎？** 看得到每次每個節點的決策嗎？
- [ ] **State 顯式嗎？** 節點之間傳的資料都在 State schema 裡嗎？
- [ ] **有 eval set 嗎？** 至少 5 個 case 涵蓋已知失敗模式嗎？
- [ ] **改了東西能量化嗎？** 一行 command 跑 eval 出 pass rate 嗎？
- [ ] **改 graph 有紀錄嗎？** 每次改有對應的 eval report 嗎？

> 沒打勾不算寫完 agent，只算寫了個 demo。

---

## 16. 收場 60 秒

> 「兩小時你們學到的不只是 LangGraph，是業界四階段演進的最新一站：
>
> **prompt → context → workflow → harness**
>
> 前半場你們寫的 agent 是 workflow engineering 的標準作品——這是 2024 的 SOTA。後半場我們把它升級到 2025–2026 的標準：trace、eval、迭代閉環。
>
> 你們今天親身體驗了一件事：**同樣的 agent，加上 harness 之後,從『跑得起來』變成『可以工程化迭代』**。沒有 harness 的 agent 永遠停在 demo 階段。
>
> 至於框架——LangGraph 在 2026 年 4 月仍是這個場景最好的選擇，但 OpenAI、Anthropic、AWS 都在追。**框架會變，但今天教你的不只是 API，是 harness 思維**。一年後你可能在用別的工具，但 trace、eval、loop 這四件事會跟著你走。
>
> 回去做兩件事：第一，把今天的 eval set 從 2 個擴充到 5 個；第二，挑一個你正在做的個人專案，畫出它的『missing harness』清單。
>
> 一個月後你回來看自己今天寫的 code 會覺得醜——那很正常，那代表你進步了。但你今天搭起來的 harness 思維還會在，這個比 code 重要。」

---

# 附錄

## A. v5 完整時程表

| 時段 | 主題 | 時長 | 動手 vs 看 demo |
|------|------|------|---------------|
| 0:00–0:05 | 開場 demo | 5min | 看 |
| 0:05–0:15 | 環境救火 | 10min | **動手** |
| 0:15–0:20 | LangGraph 心智模型 | 5min | 看 |
| 0:20–0:25 | **NEW: Python 速補（TypedDict / Annotated）** | 5min | 看 |
| 0:25–0:40 | echo bot：State / Node / compile | 15min | 後 5min **動手** |
| 0:40–0:50 | 兩節點 + Edge | 10min | 看（節省認知能量） |
| 0:50–1:00 | **NEW: LLM 物件解剖（打開黑箱）** | 10min | 看 + print |
| 1:00–1:10 | MessagesState（含 reducer 反例 demo） | 10min | 看 |
| 1:10–1:35 | Tool Calling（含 §8.2 LLM 怎麼決策的關鍵 demo） | 25min | 後 10min **動手** |
| 1:35–1:40 | **NEW: 前半場小結 + 主動破除自我懷疑** | 5min | 講 |
| 1:40–1:45 | 休息 | 5min | – |
| 1:45–1:50 | 四階段演進敘事 + 舉手調查 | 5min | 看 |
| 1:50–2:10 | Trace（含 helper 預寫） | 20min | 後 5min **動手** |
| 2:10–2:35 | Eval（含 helper 預寫，最後 10min 動手） | 25min | 後 10min **動手** |
| 2:35–2:40 | Harness loop 整合 | 5min | 看 |
| 2:40–2:45 | 框架比較 | 5min | 看 |
| 2:45–2:50 | Cheatsheet 發講義 | 5min | – |
| 2:50–2:55 | 收場 + Q&A | 5min | – |

> **時程現實檢查**：含休息總長 2 小時 55 分。**如果嚴格 2 小時必須砍**，建議砍序：(1) §14 框架比較放講義不口頭講；(2) §13 harness loop 用一張圖快速帶過；(3) §11 trace 動手時間從 5min 砍到 0；(4) §5 兩節點 + Edge 砍到 5 分鐘。**不能砍的**：§3 Python 速補、§6 LLM 物件解剖、§9 主動破除自我懷疑——這三節是初學者版的命脈。

## B. 課後練習

**Level 1（必做）**：把今天的 eval set 從 2 個 case 擴充到 5 個。涵蓋：缺失值處理、型別轉換、空 DataFrame、重複 row、單一欄位 groupby。

**Level 2**：把今天的 agent 加上 `InMemorySaver` checkpointer，讓多輪對話有記憶。

**Level 3**：研究 `graph.get_state_history()` 跟 `graph.update_state()`，實作「從歷史 checkpoint 改一個值再重跑」。這就是 §10.3 預告的 **replay** 機制。

**Level 4**：選一個你做過的個人專案，畫出它的「missing harness」清單——trace 缺什麼、eval 缺什麼。寫成 markdown 帶來下次社課討論。

## C. 學員常見 Q&A

| Q | A |
|---|---|
| `TypedDict` 跟 `dataclass` 差在哪？ | TypedDict 是 dict 的型別標註（存取用 `d["key"]`）；dataclass 是物件（存取用 `d.key`）。LangGraph 規定 State 用 TypedDict |
| 為什麼要 `compile()`？ | 把 graph 定義變成可執行物件 + 做靜態檢查（節點都連到了嗎） |
| Tool 為什麼要寫 docstring？ | LLM 完全靠 docstring 決定要不要呼叫 |
| `bind_tools` 是把工具裝到 LLM 上嗎？ | 不是「裝上去」——是把工具的「使用說明書」附在每次 LLM 呼叫的 API request 裡。LLM 看到說明書才知道有這些工具可用 |
| LLM 真的會執行 Python 嗎？ | 不會。LLM 只是「建議」呼叫某個 function。實際執行的是你的程式（或 LangGraph 的 ToolNode） |
| `MessagesState` vs 自訂 State 哪個好？ | 對話類 agent 用 `MessagesState`；結構化 pipeline 用自訂 TypedDict |
| 為什麼會 GraphRecursionError？ | LLM 一直呼叫 tool 沒收斂。通常是 prompt / tool 設計問題 |
| LangGraph 跟 LangChain 是什麼關係？ | LangChain 是 LLM 串接套件；LangGraph 是 agent workflow framework；可一起用 |
| Eval set 多大才算夠？ | 從 1 個開始就比 0 個好；有方向比有數量重要 |

## D. 延伸資源

- 官方文件：https://langchain-ai.github.io/langgraph/
- LangGraph Academy（免費）：https://academy.langchain.com/courses/intro-to-langgraph
- LangSmith（trace + eval 的 production 平台）：https://smith.langchain.com/
- Hamel Husain "Your AI Product Needs Evals"：https://hamel.dev/blog/posts/evals/
- Anthropic 對 agent harness 的工程觀點：https://www.anthropic.com/research/swe-bench-sonnet

## E. 講師 Checklist（開場前 30 分鐘）

- [ ] Colab notebook 連結測過，自己從零跑一遍沒卡
- [ ] **Notebook 內 helper functions 預先寫好**（pretty_trace、extract_tool_calls、extract_final_text、evaluate_one、run_eval_suite）—— 學員只看怎麼用
- [ ] 預備一支 demo Anthropic API key 給沒 key 的學員
- [ ] 故意有缺陷的 sales.csv 已上傳 Colab 公開連結
- [ ] 投影片開好（前半場開場 + 後半場開場兩段用）
- [ ] **複習 productive failure 紀律**：前半場無論看到學員 agent 行為多怪都不要批判
- [ ] **複習「主動破除自我懷疑」紀律**：§9 一定要講，不能省
- [ ] 後半場舉手調查的時機抓準
- [ ] 計時器，每節結束看時間別超時
- [ ] 印 cheatsheet（§15）發給學員

## F. v5 vs v4 設計差異（給未來自己看的後設說明）

v4 對「基礎 Python」的想像偏高——以為基礎 Python 包含「會寫 class、看過 type hint 就會用」。v5 校準到真實水準：寫過 function/list/dict、看過但不會寫 class、type hint 看得懂但不重視、沒寫過裝飾器、沒呼叫過 LLM API。

**v5 的關鍵改動**：

1. **新增 §3 Python 速補**——TypedDict 跟 Annotated 各 2.5 分鐘，**不能省**。原本 v4 直接寫 `class State(TypedDict)` 就上 echo bot，對沒寫過 class 的學員直接失守。

2. **新增 §6 LLM 物件解剖**——用 10 分鐘把 `AIMessage`、`response.content`、`response.tool_calls` 全部 print 出來給學員看。**這是預付的時間成本，後面 §7 §8 §11 §12 都會省下時間**。沒有這節，每次出現 `msg.tool_calls` 學員都要重新困惑。

3. **新增 §8.2 LLM 怎麼決策呼叫 tool**——3 分鐘解釋「LLM 不會執行 Python，只是建議」這個關鍵機制。沒這個解釋，整個 ReAct loop 是黑箱。

4. **新增 §9 前半場小結 + 主動破除自我懷疑**——5 分鐘明確告訴學員「等下你的 agent 行為跟旁邊不一樣不是你寫錯」。保留 productive failure 的張力（§10 舉手調查照舊），但移除自我懷疑的成本。

5. **後半場 helper functions 預先寫好**——pretty_trace、evaluate_one 等都放在 Notebook 的「helper cell」，學員只看怎麼用、不看怎麼實作。實作細節進課後練習。

6. **砍掉 §10 Replay 整節**——對只會基礎 Python 的學員太奢侈（要懂 `get_state_history`、`StateSnapshot` 物件結構、`update_state` 的 reducer 行為...）。改放課後練習 Level 3。

7. **明確區分「動手敲 code」vs「看講師 demo」**——時程表新增一欄。學員不用每行都自己敲，認知能量留給最關鍵的兩個動手任務（§4 echo bot 改大寫、§8 跑 agent 並 print messages）。

**未來改進方向**：如果工作坊 feedback 顯示前半場仍太快，可以考慮把 §8 Tool Calling 拆成兩堂社課（第一堂只到 §7 MessagesState，第二堂從 §8 開始）。今天的兩小時版本是「能塞下完整故事的最小單位」。
