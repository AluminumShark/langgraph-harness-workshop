# LangGraph Harness Workshop · 兩小時打造你的第一個 Data Analyst Agent

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/AluminumShark/langgraph-harness-workshop/blob/main/notebooks/langgraph-workshop.ipynb)

兩小時的 LangGraph + harness engineering 工作坊教材,設計給「只會基礎 Python」的學員。**不假設你寫過裝飾器、呼叫過 LLM API、看過 TypedDict**。

完成這份 notebook 之後,你會親手寫出一個會自己決定怎麼分析 CSV 的 agent,並且體會到為什麼業界從 prompt engineering 一路演進到 harness engineering——也就是「trace + eval + 迭代閉環」這套工程紀律。

## 怎麼開始 (Colab,推薦)

1. 點上面那顆 **Open In Colab** badge
2. 在 Colab 左側「鑰匙」圖示新增 secret,名稱 `ANTHROPIC_API_KEY`,值是你的 Anthropic API key
3. 從第一個 cell 開始 run,沒有 key 會跳出輸入框讓你貼

整本 notebook 已經把 helper functions 預先寫好,你只要看怎麼用、不用看怎麼實作。

## 怎麼開始 (本地 Jupyter)

```bash
# 安裝 uv (如果還沒裝)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone 並安裝相依
git clone https://github.com/AluminumShark/langgraph-harness-workshop.git
cd langgraph-harness-workshop
uv sync

# 開 notebook
uv run jupyter lab notebooks/langgraph-workshop.ipynb
```

第一個 cell 會自動偵測你不在 Colab,改用 `getpass` 提示你輸入 API key——不用先設環境變數。

## 工作坊時程

| 時段 | 主題 | 時長 | 動手 vs 看 demo |
|------|------|------|---------------|
| 0:00–0:05 | 開場 demo | 5 min | 看 |
| 0:05–0:15 | 環境救火 | 10 min | **動手** |
| 0:15–0:20 | LangGraph 心智模型 | 5 min | 看 |
| 0:20–0:25 | Python 速補 (TypedDict / Annotated) | 5 min | 看 |
| 0:25–0:40 | echo bot:State / Node / compile | 15 min | 後 5 min **動手** |
| 0:40–0:50 | 兩節點 + Edge | 10 min | 看 |
| 0:50–1:00 | LLM 物件解剖 | 10 min | 看 + print |
| 1:00–1:10 | MessagesState (含 reducer 反例 demo) | 10 min | 看 |
| 1:10–1:35 | Tool Calling | 25 min | 後 10 min **動手** |
| 1:35–1:40 | 前半場小結 + 主動破除自我懷疑 | 5 min | 講 |
| 1:40–1:45 | 休息 | 5 min | – |
| 1:45–1:50 | 四階段演進敘事 + 舉手調查 | 5 min | 看 |
| 1:50–2:10 | Trace | 20 min | 後 5 min **動手** |
| 2:10–2:35 | Eval (本工作坊最重要) | 25 min | 後 10 min **動手** |
| 2:35–2:40 | Harness loop 整合 | 5 min | 看 |
| 2:40–2:45 | 框架比較 | 5 min | 看 |
| 2:45–2:50 | Cheatsheet | 5 min | – |
| 2:50–2:55 | 收場 | 5 min | – |

含休息共 2 小時 55 分。完整教學講稿放在 [docs/lecture.md](docs/lecture.md)。

## Development

This repo is a normal modern Python project — uv-managed, with ruff + ty + pytest + nbqa. To work on it:

```bash
uv sync                               # install all deps
uv run ruff check .                   # lint
uv run ruff format .                  # format
uv run ty check                       # type check
uv run nbqa ruff notebooks/           # lint notebooks
uv run pytest                         # run tests
uv run python scripts/generate_sales_csv.py  # regenerate data/sales.csv
```

CI runs all of the above on every push to `main` and every pull request — see [.github/workflows/ci.yml](.github/workflows/ci.yml).

## License

[MIT](LICENSE).

## Acknowledgements

- **LangChain / LangGraph team** — for the framework and the LangGraph Academy
- **Hamel Husain** — `Your AI Product Needs Evals` is the canonical reference for the eval section
- The lecture's four-phase narrative (prompt → context → workflow → harness) draws on Anthropic's public engineering writing on agent harnesses
