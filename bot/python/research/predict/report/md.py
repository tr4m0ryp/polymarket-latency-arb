"""Markdown table without the tabulate dependency."""
from __future__ import annotations

import pandas as pd


def md(df: pd.DataFrame, digits: int = 3) -> str:
    def f(v):
        if isinstance(v, float):
            return "" if pd.isna(v) else f"{v:,.{digits}f}"
        return str(v)
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(f(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body]) + "\n"
