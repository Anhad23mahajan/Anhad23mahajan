"""Excel fixtures (openpyxl). Output: data/*.xlsx and mislabeled files"""
import numpy as np, pandas as pd, pathlib, shutil
from openpyxl import Workbook
OUT = pathlib.Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(11)
n = 60
dates = pd.date_range("2024-01-01", periods=n, freq="7D")
amt = [int(x) for x in rng.integers(1000, 5000, n)]

# 1. title rows above header + TOTAL row at the bottom
wb = Workbook(); ws = wb.active; ws.title = "Report"
ws["A1"] = "Sunrise NGO - Donations Report 2024"; ws["A2"] = "Prepared by Finance, generated 2025-01-05"; ws.append([])
ws.append(["Date", "Donor", "Amount", "Campaign"])
for d, a in zip(dates, amt): ws.append([d.to_pydatetime(), f"D{rng.integers(1,30)}", a, rng.choice(["Appeal", "Gala"])])
ws.append(["TOTAL", None, f"=SUM(C5:C{4+n})", None])
wb.save(OUT / "title_rows_total.xlsx")
# total as literal number (openpyxl formulas are not cached => NaN when read by pandas)
wb = Workbook(); ws = wb.active
ws.append(["Date", "Donor", "Amount", "Campaign"])
for d, a in zip(dates, amt): ws.append([d.to_pydatetime(), f"D{rng.integers(1,30)}", a, rng.choice(["Appeal", "Gala"])])
ws.append(["TOTAL", None, sum(amt), None])
wb.save(OUT / "total_row_literal.xlsx")

# 2. multiple sheets: sheet1 is a cover/summary, data is in sheet 2 and 3 (one per year)
wb = Workbook(); ws = wb.active; ws.title = "Summary"
ws.append(["Summary"]); ws.append(["See the 2024 and 2025 tabs"])
for yr in (2024, 2025):
    w = wb.create_sheet(str(yr)); w.append(["date", "sales"])
    for d in pd.date_range(f"{yr}-01-01", periods=120, freq="3D"): w.append([d.to_pydatetime(), int(rng.integers(100, 900))])
wb.save(OUT / "multi_sheet_cover_first.xlsx")
wb = Workbook(); ws = wb.active; ws.title = "2024"; ws.append(["date", "sales"])
for d in pd.date_range("2024-01-01", periods=120, freq="3D"): ws.append([d.to_pydatetime(), int(rng.integers(100, 900))])
w = wb.create_sheet("2025"); w.append(["date", "sales"])
for d in pd.date_range("2025-01-01", periods=120, freq="3D"): w.append([d.to_pydatetime(), int(rng.integers(100, 900))])
wb.save(OUT / "multi_sheet_data_first.xlsx")

# 3. merged-cell two-row header (Q1 spans three month columns)
wb = Workbook(); ws = wb.active
ws.append(["Product", "Q1", None, None, "Q2", None, None]); ws.merge_cells("B1:D1"); ws.merge_cells("E1:G1")
ws.append([None, "Jan", "Feb", "Mar", "Apr", "May", "Jun"])
for p in ["Hoodie", "Mug", "Tote", "Notebook"]: ws.append([p] + [int(x) for x in rng.integers(10, 99, 6)])
wb.save(OUT / "merged_header.xlsx")

# 4. real Excel dates + excel number formats, currency format cells, formulas with cached values absent
wb = Workbook(); ws = wb.active; ws.append(["Order Date", "Customer", "Revenue"])
for d in pd.date_range("2024-01-01", periods=80, freq="4D"):
    ws.append([d.to_pydatetime(), "C%d" % rng.integers(1, 20), int(rng.integers(100, 999))])
wb.save(OUT / "clean.xlsx")

# 5. mislabeled
shutil.copy(OUT / "donations.csv", OUT / "csv_named_xlsx.xlsx")
shutil.copy(OUT / "clean.xlsx", OUT / "xlsx_named_csv.csv")
# fake legacy .xls (OLE2 magic only) -> engine needs xlrd, not in requirements
(OUT / "legacy.xls").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 600)

# 6. blank leading rows/columns in sheet (data starts at C4)
wb = Workbook(); ws = wb.active
ws["C4"], ws["D4"], ws["E4"] = "date", "region", "sales"
for i, d in enumerate(pd.date_range("2024-01-01", periods=40, freq="5D")):
    ws.cell(row=5 + i, column=3, value=d.to_pydatetime()); ws.cell(row=5 + i, column=4, value="N"); ws.cell(row=5 + i, column=5, value=int(rng.integers(10, 99)))
wb.save(OUT / "offset_table.xlsx")
print("excel ok")
