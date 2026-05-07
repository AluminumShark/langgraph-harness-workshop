"""產生工作坊用的 sales.csv——故意設計有缺陷的資料集。

這些缺陷是刻意設計的,用來讓 LLM agent 失敗,從而展示 harness 的價值:
- region 欄位有 8 個 NaN (逼 agent 先做 inspect_data 才不會踩雷)
- date 欄位有混合格式 (測試型別轉換意識)
- 5 個重複 row (測試去重思維)
- revenue 是字串型態加錢符號 (測試型別轉換)
- East 區用低權重 + 低營收區間,確保它在乾淨資料下是「最差區域」
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


def generate_sales_csv(output_path: Path, n_rows: int = 100, seed: int = 42) -> None:
    """產生缺陷版 sales.csv。

    Args:
        output_path: 輸出檔案路徑
        n_rows: 資料筆數 (預設 100)
        seed: 隨機種子,確保每次產生的資料一樣 (用於工作坊舉手調查的可重現性)
    """
    rng = random.Random(seed)
    regions = ["East", "West", "North", "South"]

    # 故意讓 East 是表現最差的區域
    # 沒先 inspect_data 直接 groupby NaN-containing 資料的 agent 會給錯答案
    rows: list[dict[str, object]] = []
    for i in range(n_rows):
        # East 出現頻率最低,而且每筆營收區間最低——刻意設計
        region = rng.choices(regions, weights=[1, 3, 2, 2])[0]
        revenue = rng.randint(50, 200) if region == "East" else rng.randint(150, 500)
        # 混合三種日期格式,測試 agent 是否注意到型別問題
        date_fmt = rng.choice(["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"])
        date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=rng.randint(0, 365))
        rows.append(
            {
                "id": i,
                "date": date.strftime(date_fmt),
                "region": region,
                # 字串加錢符號——強迫 agent 處理型別轉換
                "revenue": f"${revenue}",
                "units": rng.randint(1, 50),
            }
        )

    df = pd.DataFrame(rows)

    # 注入 8 個 NaN 到 region 欄位 (沒先 inspect 的 agent 會踩雷)
    nan_indices = rng.sample(range(n_rows), 8)
    df.loc[nan_indices, "region"] = pd.NA

    # 加 5 個重複 row (測試去重思維)
    dup_indices = rng.sample(range(n_rows), 5)
    df = pd.concat([df, df.iloc[dup_indices]], ignore_index=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"已產生 {output_path},共 {len(df)} 筆")


if __name__ == "__main__":
    generate_sales_csv(Path(__file__).parent.parent / "data" / "sales.csv")
