"""產生 demo 用的 sales.csv(100 筆,含少量 NaN)。

設計重點:
- region 故意讓 South 平均 revenue 最低,讓 §12 的 eval 有東西比
- 在 region / revenue 欄位混 5-10 個 NaN,讓 inspect_data 看得到
- 每次跑都用相同 seed,確保結果可重現
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
N_ROWS = 100
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sales.csv"

REGIONS = ["East", "West", "North", "South"]
PRODUCTS = ["Widget", "Gadget", "Gizmo", "Doohickey"]


def main() -> None:
    rng = random.Random(SEED)

    base_day = date(2025, 1, 1)
    rows: list[dict] = []
    for _ in range(N_ROWS):
        day = base_day + timedelta(days=rng.randint(0, 89))
        region = rng.choice(REGIONS)
        product = rng.choice(PRODUCTS)
        units = rng.randint(1, 50)

        # South 平均故意偏低
        unit_price = rng.uniform(8, 18) if region == "South" else rng.uniform(20, 60)
        revenue = round(units * unit_price, 2)

        rows.append(
            {
                "date": day.isoformat(),
                "region": region,
                "product": product,
                "units": units,
                "revenue": revenue,
            }
        )

    df = pd.DataFrame(rows)

    # 故意混入 NaN:5 個在 region、5 個在 revenue
    nan_region_idx = rng.sample(range(N_ROWS), 5)
    nan_revenue_idx = rng.sample(range(N_ROWS), 5)
    df.loc[nan_region_idx, "region"] = pd.NA
    df.loc[nan_revenue_idx, "revenue"] = pd.NA

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"已寫入 {OUT_PATH}({len(df)} 筆)")
    print(f"region NaN: {df['region'].isna().sum()},revenue NaN: {df['revenue'].isna().sum()}")


if __name__ == "__main__":
    main()
