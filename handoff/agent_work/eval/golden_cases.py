"""Golden NL->SQL cases for Lumen's demo shop data.

Each case: a plain-English question, and an independent *pandas* computation of the true answer
(not SQL, so the golden value does not share bugs with the DuckDB path). Used to score
(a) the real Gemini pipeline when a key is present, and (b) offline stubs in unit tests.
"""
import sys
import pandas as pd
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
from app import analytics as A

df = A.demo_df()
df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
df["year"] = df["order_date"].dt.year

def top(series):  # (label, value) of the max
    return series.idxmax(), float(series.max())

CASES = [
    dict(q="What is the total revenue?", kind="scalar", truth=float(df.amount.sum())),
    dict(q="How many orders are there in total?", kind="scalar", truth=float(len(df))),
    dict(q="Which product brings in the most revenue?", kind="label", truth=top(df.groupby("product").amount.sum())[0]),
    dict(q="Which region has the lowest total sales?", kind="label", truth=df.groupby("region").amount.sum().idxmin()),
    dict(q="What was the average order value?", kind="scalar", truth=float(df.amount.mean())),
    dict(q="How many hoodies were sold?", kind="scalar", truth=float(df.loc[df["product"] == "Hoodie", "quantity"].sum())),
    dict(q="What was total revenue in 2025?", kind="scalar", truth=float(df.loc[df.year == 2025, "amount"].sum())),
    dict(q="Which month had the highest revenue?", kind="label", truth=top(df.groupby("month").amount.sum())[0].strftime("%Y-%m")),
    dict(q="What share of revenue comes from the Campus region?", kind="scalar", truth=float(df.loc[df.region == "Campus", "amount"].sum() / df.amount.sum())),
    dict(q="Which product sold the most units?", kind="label", truth=df.groupby("product").quantity.sum().idxmax()),
    dict(q="How much revenue did Mugs bring in online?", kind="scalar", truth=float(df.loc[(df["product"] == "Mug") & (df.region == "Online"), "amount"].sum())),
    dict(q="How many distinct products do we sell?", kind="scalar", truth=float(df["product"].nunique())),
    dict(q="What was the biggest single order?", kind="scalar", truth=float(df.amount.max())),
    dict(q="Revenue by region", kind="table", truth=df.groupby("region").amount.sum().round(2).to_dict()),
    dict(q="Total revenue per product in 2024", kind="table", truth=df[df.year == 2024].groupby("product").amount.sum().round(2).to_dict()),
    dict(q="How many orders were on weekends?", kind="scalar", truth=float((df.order_date.dt.dayofweek >= 5).sum())),
    dict(q="What day had the highest total revenue?", kind="label", truth=top(df.groupby("order_date").amount.sum())[0].strftime("%Y-%m-%d")),
    dict(q="Average quantity per order for notebooks", kind="scalar", truth=float(df.loc[df["product"] == "Notebook", "quantity"].mean())),
    dict(q="Which region sold the most hoodies by revenue?", kind="label", truth=df[df["product"] == "Hoodie"].groupby("region").amount.sum().idxmax()),
    dict(q="Revenue growth 2025 vs 2024 in percent", kind="scalar", truth=float((df[df.year == 2025].amount.sum() / df[df.year == 2024].amount.sum() - 1) * 100)),
]

if __name__ == "__main__":
    for c in CASES:
        print(f"{c['kind']:7} {c['q']:55} -> {c['truth'] if c['kind']!='table' else '{...%d rows}' % len(c['truth'])}")
    print(len(CASES), "cases")
