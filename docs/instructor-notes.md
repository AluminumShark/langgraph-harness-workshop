# 講師備課筆記

> 給開課前的你看的——不是給學員看的。完整講稿在 [lecture.md](lecture.md)。

---

## 開場前 30 分鐘 Checklist

- [ ] **Colab notebook 連結測過**:自己從零跑一遍沒卡。注意 `notebooks/langgraph-workshop.ipynb` 第三個 cell 的 `DATA_URL` 要指向你們社團真正的 GitHub repo (預設是 `NTUAI-CLUB/langgraph-harness-workshop` placeholder,如果還沒換,sales.csv 會 404)
- [ ] **預備一支 demo Anthropic API key** 給沒 key 的學員
- [ ] **故意有缺陷的 sales.csv 已上傳公開連結** (commit 在 `data/sales.csv`,raw GitHub URL 即可)
- [ ] **投影片開好** (前半場開場 + 後半場開場兩段用)
- [ ] **複習 productive failure 紀律**——前半場無論看到學員 agent 行為多怪都不要批判 (見下節)
- [ ] **複習主動破除自我懷疑紀律**——§9 一定要講,不能省 (見下節)
- [ ] **後半場舉手調查的時機抓準** (§10.1)
- [ ] **計時器**,每節結束看時間別超時
- [ ] **印 cheatsheet** (§15) 發給學員

---

## 不能省的三節 (v5 命脈)

對只會基礎 Python 的學員,下面三節是 v5 教案的命脈,**省掉直接失守**:

1. **§3 Python 速補 (TypedDict + Annotated)**:5 分鐘。原本 v4 直接寫 `class State(TypedDict)` 就上 echo bot,對沒寫過 class 的學員直接斷線
2. **§6 LLM 物件解剖**:10 分鐘。把 `AIMessage`、`response.content`、`response.tool_calls` 全部 print 出來給學員看。**這是預付的時間成本**,後面 §7 §8 §11 §12 都會省下時間
3. **§9 主動破除自我懷疑**:5 分鐘。明確告訴學員「等下你的 agent 跟旁邊不一樣不是你寫錯」。保留 §10 productive failure 的張力,但移除自我懷疑的成本

---

## Productive Failure 紀律 (前半場)

**核心紀律**:前半場 (§1–§8) agent 跑出怪結果時,你**只能說一句話**:

> 「對,agent 就是這樣,每次跑可能不太一樣。」

**不要做**:
- 解釋為什麼這次跑出 East、那次跑出 West (留到 §11.4 trace 時再用對比解釋)
- 主動加上 system prompt「修好」(這是 §12.5 的高潮,提前修掉就沒戲)
- 讓學員以為這是「他寫錯了」(§9 才會處理)

**為什麼這個紀律重要**:整堂課的敘事弧是「workflow engineering 跑得起來但不夠 → harness engineering 才夠」。前半場 agent 的不穩定**就是後半場舉手調查的素材**。提前修掉 = §10.1 沒得舉手 = §10.2 四階段演進敘事失去落地點。

---

## §9 主動破除自我懷疑紀律

**這節 5 分鐘必講,不能用「下課再講」帶過**。原因:

- 前半場學員看到 agent 行為亂跳,**心裡會想「是不是我寫錯了」**
- 中場休息 5 分鐘他們會去問同學、會去 ChatGPT 問——**這些懷疑會擴散**
- §9 在中場休息前**先主動破除**,把「不穩定是 LLM 本質、業界都在處理」的訊息打進去
- 這樣 §10.1 舉手調查時學員心理是「啊原來這就是 productive failure 的素材」,而不是「我跟旁邊都寫錯了」

**講話節奏**(逐字稿建議):

> 「OK,前半場告一段落。我要先說一件**很重要**的事:剛才大家跑出來的 agent,結果可能不太一樣——有人跑出 East,有人跑出 West,有人跑兩次答案不一樣。**這不是你寫錯了。** 這是 LLM agent 的**正常變異**——同一個程式、同一份資料,每次跑可能走不同路徑、做不同決定。這是 LLM 的本質特性,**業界所有人都在處理這件事**。後半場我們就要學業界怎麼處理。休息 5 分鐘。」

---

## 各節時程檢查 (含緩衝)

| 時段 | 主題 | 容許上限 | 超時警訊 |
|------|------|---------|---------|
| 0:00–0:15 | 開場 + 環境救火 | 0:15 | API key 過 5 分鐘還沒過關 → 直接 fork 你準備好的「已能跑」版本 |
| 0:15–0:25 | 心智模型 + Python 速補 | 0:25 | 學員糾結 TypedDict vs dataclass → 「LangGraph 規定用 TypedDict,其他今天不討論」 |
| 0:25–0:50 | echo bot + 兩節點 | 0:50 | 動手時間沒人寫得出 → 直接秀解答,**不要全班等** |
| 0:50–1:00 | LLM 物件解剖 | 1:00 | 不能砍——後面所有 LLM 操作都靠這節打底 |
| 1:00–1:35 | MessagesState + Tool Calling | 1:35 | §8.4 完整實作沒 compile 起來 → 要學員直接跑你準備好的版本,**先 §8.7 跑起來再回頭講原理** |
| 1:35–1:40 | §9 主動破除自我懷疑 | 1:40 | 不能砍 |
| 1:45–1:50 | 四階段演進 | 1:50 | 學員問「我們現在在哪一階段」 → 「workflow,後半場進 harness」 |
| 1:50–2:10 | Trace | 2:10 | 動手時間 5 分鐘可砍到 0 (改成講師示範 3 次) |
| 2:10–2:35 | Eval | 2:35 | **這節最重要,寧可砍後面也不要砍這個**。§12.4 baseline 跑起來太久 → 跳過,直接 §12.5 看數字變化 |
| 2:35–2:55 | 收尾 + Q&A | 2:55 | §14 框架比較放講義不口頭 |

---

## 砍時建議 (如果嚴格 2 小時)

按優先順序砍:

1. **§14 框架比較**放講義不口頭講 (省 5 分鐘)
2. **§13 harness loop** 用一張圖快速帶過 (省 3 分鐘)
3. **§11 trace 動手時間**從 5min 砍到 0,改成講師示範 (省 5 分鐘)
4. **§5 兩節點 + Edge** 砍到 5 分鐘 (省 5 分鐘)

**不能砍的**:§3 Python 速補、§6 LLM 物件解剖、§9 主動破除自我懷疑——這三節是初學者版的命脈。

---

## 常見 derail 模式 + 救援

| 學員問題 | 短答 (15 秒內) | 長答放哪 |
|---------|-------------|---------|
| TypedDict 跟 dataclass 差在哪? | 存取方式不同;LangGraph 規定 TypedDict | docs/lecture.md §C |
| 為什麼要 compile()? | 把定義變執行物件 + 靜態檢查 | §4.4 |
| Tool 為什麼要寫 docstring? | LLM 完全靠 docstring 決定要不要呼叫 | §8.3 |
| LLM 真的會執行 Python 嗎? | **不會**,只是建議呼叫 | §8.1 |
| 為什麼會 GraphRecursionError? | LLM 一直呼叫 tool 沒收斂,通常是 prompt / tool 設計問題 | §15 雷 |
| LangGraph 跟 LangChain 是什麼關係? | LangChain 是 LLM 串接套件;LangGraph 是 agent workflow framework;可一起用 | docs/lecture.md §C |
| Eval set 多大才算夠? | 從 1 個開始就比 0 個好;有方向比有數量重要 | §12.6 |

---

## Colab 掛掉的 backup 計畫

如果 Colab 大規模當機:

1. **降級到本地 Jupyter**:Cell 1 的 API key fallback 已經支援 `getpass`——學員 `git clone` 你的 repo,`uv sync`,`uv run jupyter lab` 即可
2. **如果學員機器沒裝 uv**:給他們你電腦上的環境,投影出去全班一起看 (productive failure 紀律仍然要守——`graph.invoke()` 結果不一定一樣,維持原本敘事)
3. **如果連你電腦都掛**:直接跳到 §10–§16 純講授,把 §1–§8 改成「我先示範完整 demo,大家回家跑」——課後練習 Level 0 變成「把今天 demo 過的 agent 自己跑一遍」

---

## v5 vs v4 設計差異 (給未來自己看)

v4 對「基礎 Python」的想像偏高——以為基礎 Python 包含「會寫 class、看過 type hint 就會用」。v5 校準到真實水準:寫過 function/list/dict、看過但不會寫 class、type hint 看得懂但不重視、沒寫過裝飾器、沒呼叫過 LLM API。

**v5 關鍵改動**:

1. 新增 §3 Python 速補 (TypedDict + Annotated)
2. 新增 §6 LLM 物件解剖 (預付 10 分鐘換後面 §7 §8 §11 §12 的時間)
3. 新增 §8.2 LLM 怎麼決策呼叫 tool (3 分鐘破除黑箱)
4. 新增 §9 主動破除自我懷疑 (5 分鐘心理安全)
5. 後半場 helper functions 預先寫好 (學員只看怎麼用)
6. 砍掉 Replay 整節 (對基礎學員太奢侈,改放課後練習 Level 3)
7. 明確區分「動手敲」vs「看講師 demo」(時程表新增一欄)

---

## 工具鏈速查

```bash
uv sync                              # 安裝
uv run python scripts/generate_sales_csv.py  # 重新產生 sales.csv
uv run jupyter lab notebooks/langgraph-workshop.ipynb  # 本地開 notebook
uv run pytest                        # 跑單元測試 (helpers + eval_runner)
uv run ruff check . && uv run ruff format --check .   # lint + format
uv run ty check                      # 型別檢查
uv run nbqa ruff notebooks/          # notebook lint
```

`src/langgraph_harness_workshop/` 跟 notebook 內聯的 helper 1:1 對應——改 helper 邏輯記得兩邊都改。
