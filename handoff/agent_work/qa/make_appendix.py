import json
a = json.load(open("results_pd3.json")); a.update(json.load(open("results_pd3_big.json")))
b = json.load(open("results_patched.json")); b.update(json.load(open("results_patched_big.json")))
p2 = json.load(open("results_pd2.json")); p2.update(json.load(open("results_pd2_big.json")))
notes = {
 "accents_nfd.csv": "P1-14 header mangled", "ambig_dmy_halfyear.csv": "P1-01", "ambig_dmy_small.csv": "P1-01", "cp1252_euro.csv": "P1-15", "csv_named_xlsx.xlsx": "P2-08", "daily_70d_midweek.csv": "P1-07",
 "donations.csv": "P1-08 (Dec 2024 dropped)", "edge_datelike_text.csv": "P1-18 version->date", "edge_dup_cols.csv": "P2-09", "edge_gappy_unsorted.csv": "zero-filled gaps", "edge_huge_values.csv": "P2-16 1e300",
 "edge_inf_values.csv": "P2-16 inf", "edge_reserved_cols.csv": "P1-21 SQL guard", "edge_trailing_blank.csv": "P2-12 whitespace rows", "edge_two_rows.csv": "P1-11 forecast from 2 rows",
 "edge_year_only.csv": "P1-19 yearly bucketed monthly", "ends_dec30.csv": "P1-08", "epoch_seconds.csv": "ok", "european.csv": "P1-02", "european_nothousands.csv": "P1-02", "expenses_currency.csv": "P1-03",
 "hindi_headers.csv": "P1-14", "ids_only_numeric.csv": "P1-12", "ids_plus_amount.csv": "P1-12 (dropdown)", "inventory.csv": "P1-12", "legacy.xls": "P1-06", "merged_header.xlsx": "P2-10", "metric_names.csv": "P1-13",
 "monthly_names.csv": "P2-14 top-8 cut", "multi_sheet_cover_first.xlsx": "P1-05", "multi_sheet_data_first.xlsx": "P1-05", "offset_table.xlsx": "P1-04", "pct_bool_thousands.csv": "P2-14 True/False labels", "starts_mid_month.csv": "P1-07",
 "title_rows_total.xlsx": "P1-04", "total_row_literal.xlsx": "P1-04 double count", "tz_mixed_offsets.csv": "P1-16", "tz_utc.csv": "P1-07", "us_mdy_halfyear.csv": "P1-07", "utf16_tab.txt.csv": "P1-15",
 "year_month_ints.csv": "P1-12 month as metric", "big_250k_truncation.csv": "P1-10 silent truncation", "big_over_25mb.csv": "413 ok", "big_under_25mb_wide.csv": "slow (P1-17)", "big_200k.csv": "slow (P1-17)", "big_100k.xlsx": "slow (P1-17)",
 "edge_binary_garbage.csv": "P2-08 (400 cryptic)", "edge_html_page.csv": "400", "edge_empty.csv": "400 ok", "edge_header_only.csv": "400 ok", "edge_newlines_only.csv": "400 ok"}
print("| fixture | size | base HTTP | base secs | base metric / date | patched HTTP | patched metric / date | pd2.2.3 = pd3.0.6? | note |"); print("|---|---:|---|---:|---|---|---|---|---|")
for f in sorted(a):
    x, y, z = a[f], b.get(f, {}), p2.get(f, {})
    md = lambda r: (f"{r['summary']['metric']} / {r['summary']['date']}" if "summary" in r else (r.get("detail") or "")[:46])
    same = "yes" if (md(x) == md(z) and x.get("status") == z.get("status")) else "differs"
    print(f"| {f} | {x['size']:,} | {x.get('status')} | {x.get('upload_secs')} | {md(x)} | {y.get('status')} | {md(y)} | {same} | {notes.get(f, '')} |")
