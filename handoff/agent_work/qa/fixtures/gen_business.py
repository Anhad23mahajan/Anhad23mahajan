"""Realistic small-business / NGO files. Output: data/*.csv"""
import numpy as np, pandas as pd, pathlib
OUT = pathlib.Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(42)

# 1. donations: donor, date, amount, campaign, channel  (24 months, trend + year-end spike)
n = 3000
dates = pd.to_datetime("2023-01-01") + pd.to_timedelta(rng.integers(0, 730, n), unit="D")
amt = np.round(rng.lognormal(3.5, 1.0, n), 2)
amt[dates.month == 12] *= 2
pd.DataFrame({"donor": [f"Donor {i}" for i in rng.integers(1, 400, n)], "date": dates.strftime("%Y-%m-%d"),
              "amount": amt, "campaign": rng.choice(["Annual Appeal", "Giving Tuesday", "Gala", "Monthly"], n, p=[.4, .2, .1, .3]),
              "channel": rng.choice(["Online", "Cheque", "Cash", "Bank transfer"], n)}).sort_values("date").to_csv(OUT / "donations.csv", index=False)

# 2. inventory: no date column at all
m = 120
pd.DataFrame({"sku": [f"SKU-{1000+i}" for i in range(m)], "qty": rng.integers(0, 300, m), "reorder_level": rng.integers(10, 60, m),
              "supplier": rng.choice(["Acme", "Globex", "Initech", "Hooli"], m), "unit_cost": np.round(rng.uniform(1, 50, m), 2)}).to_csv(OUT / "inventory.csv", index=False)

# 3. expenses: currency symbols, thousands separators, negatives in parentheses and with minus
n = 400
d = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D")
v = np.round(rng.uniform(20, 2500, n), 2)
def fmt(x, i):
    s = f"${x:,.2f}"
    if i % 25 == 0: return f"(${x:,.2f})"       # refund shown in parentheses
    if i % 40 == 0: return f"-${x:,.2f}"
    return s
pd.DataFrame({"date": d.strftime("%Y-%m-%d"), "vendor": rng.choice(["Staples", "AWS", "Uber", "Landlord", "Payroll Co"], n),
              "category": rng.choice(["Office", "Cloud", "Travel", "Rent", "Payroll"], n), "amount": [fmt(x, i) for i, x in enumerate(v)]}
             ).sort_values("date").to_csv(OUT / "expenses_currency.csv", index=False)

# 4. monthly summary table with month NAMES (very common spreadsheet layout)
pd.DataFrame({"Month": ["January","February","March","April","May","June","July","August","September","October","November","December"],
              "Revenue": [12000,13500,12800,15000,16200,15800,17000,18100,17500,19000,21000,25000]}).to_csv(OUT / "monthly_names.csv", index=False)

# 5. weekday names
pd.DataFrame({"weekday": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]*4, "sales": rng.integers(100, 900, 28)}).to_csv(OUT / "weekday_names.csv", index=False)

# 6. 70 days of daily sales ending mid-week (weekly resample => partial last week)
dd = pd.date_range("2025-03-03", "2025-05-14")   # Mon .. Wed
pd.DataFrame({"date": dd.strftime("%Y-%m-%d"), "sales": np.round(rng.normal(1000, 50, len(dd)), 0)}).to_csv(OUT / "daily_70d_midweek.csv", index=False)

# 7. 14 months of data that ends on Dec 30 (Dec 31 had no sales)
dd = pd.date_range("2024-11-01", "2025-12-30")
pd.DataFrame({"date": dd.strftime("%Y-%m-%d"), "revenue": np.round(rng.normal(500, 30, len(dd)), 0)}).to_csv(OUT / "ends_dec30.csv", index=False)

# 8. data starts mid-month (first month partial)
dd = pd.date_range("2024-03-28", "2025-03-31")
pd.DataFrame({"date": dd.strftime("%Y-%m-%d"), "revenue": np.round(rng.normal(500, 30, len(dd)), 0)}).to_csv(OUT / "starts_mid_month.csv", index=False)

# 9. metric-name heuristics: wages (matches 'age'), corporate_sales (matches 'rate'), page_views, package_count
n = 200
dd = pd.date_range("2024-01-01", periods=n, freq="3D")
pd.DataFrame({"date": dd.strftime("%Y-%m-%d"), "wages": rng.integers(800, 1200, n), "corporate_sales": rng.integers(100, 200, n),
              "page_views": rng.integers(1000, 2000, n), "region": rng.choice(["N", "S"], n)}).to_csv(OUT / "metric_names.csv", index=False)

# 10. ids as numbers: shuffled invoice numbers, 6-digit pincode, phone numbers, plus an unhinted amount-less file
n = 300
pd.DataFrame({"invoice_number": rng.permutation(np.arange(100200, 100200 + n * 3, 3)), "pincode": rng.choice([110001, 400001, 560001, 600001], n),
              "mobile": rng.integers(7_000_000_000, 9_999_999_999, n), "city": rng.choice(["Delhi", "Mumbai", "Bengaluru", "Chennai"], n)}).to_csv(OUT / "ids_only_numeric.csv", index=False)
pd.DataFrame({"invoice_number": rng.permutation(np.arange(100200, 100200 + n * 3, 3)), "pincode": rng.choice([110001, 400001, 560001, 600001], n),
              "order_date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"), "amount": rng.integers(100, 1000, n)}).to_csv(OUT / "ids_plus_amount.csv", index=False)

# 11. year / month / quarter integer columns + flag, with no hinted metric
n = 240
pd.DataFrame({"year": np.repeat([2022, 2023, 2024, 2025], 60), "month": np.tile(np.arange(1, 13), 20), "visitors": rng.integers(50, 500, n),
              "is_member": rng.integers(0, 2, n), "branch": rng.choice(["A", "B", "C"], n)}).to_csv(OUT / "year_month_ints.csv", index=False)

# 12. correlation ordering for the insights() best-correlation bug: strong first, weak later
n = 400
x = rng.normal(0, 1, n); amount = 100 + 20 * x + rng.normal(0, 2, n)
pd.DataFrame({"date": pd.date_range("2024-01-01", periods=n).strftime("%Y-%m-%d"), "amount": amount, "strong_driver": x * 10 + rng.normal(0, 1, n),
              "weak_driver": 0.55 * x + rng.normal(0, 1, n)}).to_csv(OUT / "corr_order.csv", index=False)

# 13. percentages & booleans & thousand-sep text numbers
n = 150
pd.DataFrame({"date": pd.date_range("2024-01-01", periods=n, freq="W").strftime("%Y-%m-%d")[:n], "revenue": [f"{x:,}" for x in rng.integers(1000, 90000, n)],
              "conversion_pct": [f"{x:.1f}%" for x in rng.uniform(1, 9, n)], "repeat_customer": rng.choice(["Yes", "No"], n), "paid": rng.choice([True, False], n)}).to_csv(OUT / "pct_bool_thousands.csv", index=False)
print("business ok")
