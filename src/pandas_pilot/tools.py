"""Data analyst agent 用的兩個工具。"""

from __future__ import annotations

import io

import pandas as pd
from langchain_core.tools import tool


@tool
def inspect_data(path: str) -> str:
    """檢查 CSV 資料品質。執行任何 groupby/filter/agg 之前**必須**先呼叫
    這個工具,了解資料的形狀、欄位、缺失值情況。

    參數:
        path: CSV 檔案路徑
    回傳:
        字串,包含 shape、欄位、缺失值、前五筆樣本
    """
    df = pd.read_csv(path)

    buf = io.StringIO()
    buf.write(f"shape: {df.shape}\n")
    buf.write(f"columns: {list(df.columns)}\n")
    buf.write("\ndtypes:\n")
    buf.write(df.dtypes.to_string())
    buf.write("\n\nmissing values per column:\n")
    buf.write(df.isna().sum().to_string())
    buf.write("\n\nhead(5):\n")
    buf.write(df.head(5).to_string())
    return buf.getvalue()


@tool
def run_pandas(path: str, code: str) -> str:
    """對 CSV 執行 pandas 分析程式碼,例如 groupby、filter、agg、sort 等。
    讀好的 DataFrame 以 `df` 變數提供,可直接在 code 中使用。

    參數:
        path: CSV 檔案路徑
        code: 一段 pandas expression(例如 "df.groupby('region')['revenue'].mean()")
    回傳:
        執行結果的字串(超過 2000 字會截斷)
    """
    # ⚠️ 注意:eval() 在 production 是嚴重安全問題
    # 此處為了工作坊講解簡化使用,實務上請改 sandbox / RestrictedPython / e2b
    df = pd.read_csv(path)
    try:
        result = eval(code, {"df": df, "pd": pd})
    except Exception as exc:
        return f"執行錯誤:{type(exc).__name__}: {exc}"

    text = str(result)
    if len(text) > 2000:
        text = text[:2000] + "\n... (output truncated)"
    return text
