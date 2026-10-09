"""BUG-14..18  metric / aggregation / date-column selection heuristics.
run: /home/user/work/venv/bin/python -I r06_metric_choice.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
hdr("A) which column does Lumen call 'the metric'? (truth in brackets)")
for f, truth in [("inventory.csv", "qty (or qty*unit_cost); summing unit_cost is meaningless"), ("ids_only_numeric.csv", "none (invoice_number/pincode/mobile are identifiers)"),
                 ("ids_plus_amount.csv", "amount; but invoice_number & pincode are offered in the forecast dropdown"), ("year_month_ints.csv", "visitors (year/month are calendar parts)"),
                 ("edge_reserved_cols.csv", "ambiguous"), ("edge_year_only.csv", "amount, by YEAR (8 yearly points)")]:
    p, ins, ch = analyse(load(f)); k = [(x["label"], round(x["value"], 1)) for x in p["kpis"][1:3]]
    print(f"{f:24s} metric={p['metric']!s:15s} date={p['date']!s:8s} metric_cols={p['metric_cols']} KPIs={k}\n{'':24s} truth: {truth}")
hdr("B) sum-vs-mean heuristic agg_for(): regex 'age|rate|temp' matches INSIDE words")
for name in ["wages", "page_views", "package_count", "usage_kwh", "message_count", "storage_cost", "damage_cost", "mileage", "corporate_sales", "generated_revenue", "separate_fees", "temporary_staff_cost", "attempts", "stage_total", "coverage_amount", "image_count",
             "average_sales", "unit_price", "conversion_rate", "age", "balance", "score"]:
    print(f"   {name:22s} -> {A.agg_for(name)}")
p, ins, ch = analyse(load("metric_names.csv")); print("\nmetric_names.csv (date, wages, corporate_sales, page_views): KPI label =", [k['label'] for k in p['kpis']][1], "<- should be 'Total corporate_sales'")
hdr("C) yearly table (year, amount x3 rows/year, 2019-2026): Lumen buckets it MONTHLY -> 84 points, 8 non-zero")
p, ins, ch = analyse(load("edge_year_only.csv")); line = [c for c in ch if c['type'] == 'line'][0]
print("chart:", line['title'], "points:", len(line['y']), "non-zero:", sum(1 for v in line['y'] if v), "| KPI:", [(k['label'], k.get('note')) for k in p['kpis'][2:]], "| insight:", [i['title'] for i in ins])
hdr("D) 'Mon-YY' / 'Month YYYY' labels are not recognised as dates (very common in small-business sheets)")
for lbl, f in [("Jan-25", lambda m: pd.Timestamp(2025, m, 1).strftime("%b-%y")), ("Jan 2025", lambda m: pd.Timestamp(2025, m, 1).strftime("%b %Y")), ("January 2025", lambda m: pd.Timestamp(2025, m, 1).strftime("%B %Y")), ("2025-01", lambda m: f"2025-{m:02d}")]:
    df = A.preprocess_df(pd.DataFrame({"month": [f(m) for m in range(1, 13)], "revenue": range(100, 1300, 100)})); print(f"   {lbl:14s} -> kind={A.kind(df['month'])}")
