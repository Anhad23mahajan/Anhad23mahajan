"""BUG-07/08/09  Excel layouts: title rows above header, TOTAL row double counted, only first sheet read, offset tables.
run: /home/user/work/venv/bin/python -I r04_excel_layout.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
for name, truth in [("title_rows_total.xlsx", "header is on row 4 ('Date','Donor','Amount','Campaign'); data rows 5.. ; last row is TOTAL"),
                    ("offset_table.xlsx", "table starts at C4; header 'date','region','sales'"),
                    ("total_row_literal.xlsx", "has a literal TOTAL row at the bottom (sum = 196,030); true total of data rows = 196,030"),
                    ("multi_sheet_data_first.xlsx", "sheets '2024' and '2025' each have 120 rows; true total = 114,695"),
                    ("multi_sheet_cover_first.xlsx", "sheet 1 is a cover note; the data is on sheets 2024/2025"),
                    ("merged_header.xlsx", "two-row header, Q1 spans B:D")]:
    hdr(name + "  ->  " + truth); df = load(name); p, ins, ch = analyse(df)
    print("columns:", list(df.columns)); print("rows:", len(df), "| metric:", p["metric"], "| date:", p["date"])
    print("KPIs:", [(k["label"], round(k["value"], 1)) for k in p["kpis"]]); print("first row:", df.iloc[0].tolist()[:5]); print("last row:", df.iloc[-1].tolist()[:5])
x = pd.ExcelFile(DATA / "multi_sheet_data_first.xlsx"); print("\nsheets in file:", x.sheet_names, "-> Lumen reads only sheet_name=0 (pd.read_excel default) and never tells the user")
