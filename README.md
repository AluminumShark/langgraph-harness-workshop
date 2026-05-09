# pandas-pilot

> LangGraph 工作坊配套:寫出你的第一個 Data Analyst Agent

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AluminumShark/langgraph-harness-workshop/blob/main/notebooks/workshop.ipynb)

點上面的 badge 直接在 Colab 開 notebook,不需要本地安裝。

## 這是什麼

LangGraph 工作坊的學員配套程式碼。一個 90 分鐘的工作坊,從零打造一個會分析 CSV 的 ReAct agent,並親手體驗 agent 的 stochastic 本性、學會用 trace + eval 把它當工程系統管。

工作坊重點:

- 跟著講師現場跑 notebook,**看講師打開回傳物件**——這比看 slide 還重要
- 故意讓學員體驗「同樣的問題、同樣的程式,Agent 回三種答案」這個現實
- 教 trace 與 eval 這兩個讓 agent 變成可工程化系統的關鍵紀律

## Colab 玩法(學員)

1. 點上面的 **Open In Colab** badge
2. 右上角 **「Copy to Drive」** 存一份到自己的 Drive
3. 到 https://aistudio.google.com/apikey 拿一把免費的 Gemini API key
4. Colab 左側鑰匙圖示 → **Add new secret**:
   - 名稱:`GOOGLE_API_KEY`
   - 值:剛才拿到的 key
   - 打開 **「Notebook access」** 開關 ← 常見漏點,沒打開會讀不到
5. 跑第一個 cell 確認接通
6. 跟著講師往下跑

## 本地開發(進階)

如果你想 fork 修改、或在本地跑而不是 Colab:

```bash
# 1. 裝 uv (如果還沒裝)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. clone
git clone https://github.com/AluminumShark/langgraph-harness-workshop.git
cd langgraph-harness-workshop

# 3. 裝相依
uv sync

# 4. 設定 API key
export GOOGLE_API_KEY="你的 key"

# 5. 跑 notebook
uv run jupyter notebook notebooks/workshop.ipynb

# 或跑測試
uv run pytest

# Lint / format
uv run ruff check .
uv run ruff format .

# Type check(ty 仍在 preview)
uv run ty check src/
```

## 目錄結構

```
pandas-pilot/
├── README.md
├── pyproject.toml
├── .gitignore
├── .python-version
├── notebooks/
│   └── workshop.ipynb       # 學員主要操作的檔案(§0-§14)
├── data/
│   └── sales.csv            # demo 資料(100 筆,含少量 NaN)
├── scripts/
│   └── generate_sales_csv.py  # 重新產生 sales.csv 的 script
├── src/
│   └── pandas_pilot/
│       ├── __init__.py
│       ├── tools.py         # @tool 定義(inspect_data、run_pandas)
│       ├── graph.py         # build_graph()
│       ├── trace.py         # pretty_trace()
│       └── eval.py          # EVAL_CASES、evaluate_one、run_eval_suite
└── tests/
    └── test_smoke.py        # smoke test
```

## 工作坊涵蓋範圍

- §0 開場
- §1 環境救火(API key、套件安裝)
- §2 LangGraph 心智模型(Node / Edge / State)
- §3 Python 速補(type hint / TypedDict / Annotated / `@tool`)
- §4 第一個 graph: echo bot
- §5 兩節點 + 邊
- §6 LLM 物件解剖
- §7 MessagesState
- §8 Tool Calling(前半場核心)
- §9 前半場小結
- §10 後半場開場(harness 概念)
- §11 Trace
- §12 Eval(baseline → 加 system prompt 重跑)
- §13 Harness Loop 概念
- §14 收場 + 課後練習提示

## 安全告誡

`run_pandas` 用 `eval()` 跑 LLM 生出的 code——這在 production 是嚴重漏洞。實務上請用 sandbox / RestrictedPython / e2b。本專案是教學用,故意簡化以便講解。

## License

MIT
