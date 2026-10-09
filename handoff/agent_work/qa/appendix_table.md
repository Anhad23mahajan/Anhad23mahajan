| fixture | size | base HTTP | base secs | base metric / date | patched HTTP | patched metric / date | pd2.2.3 = pd3.0.6? | note |
|---|---:|---|---:|---|---|---|---|---|
| accents_nfc.csv | 6,336 | 200 | 0.02 | montant_ttc / date_de_création | 200 | montant_ttc / date_de_création | yes |  |
| accents_nfd.csv | 6,338 | 200 | 0.1 | montant_ttc / date_de_cre_ation | 200 | montant_ttc / date_de_création | yes | P1-14 header mangled |
| ambig_dmy_halfyear.csv | 2,726 | 200 | 0.1 | sales / date | 200 | sales / date | yes | P1-01 |
| ambig_dmy_small.csv | 191 | 200 | 0.05 | sales / date | 200 | sales / date | yes | P1-01 |
| big_100k.xlsx | 2,761,788 | 200 | 9.46 | amount / date | 200 | amount / date | yes | slow (P1-17) |
| big_200k.csv | 7,405,771 | 200 | 6.62 | amount / date | 200 | amount / date | yes | slow (P1-17) |
| big_250k_truncation.csv | 9,257,696 | 200 | 8.48 | amount / date | 200 | amount / date | yes | P1-10 silent truncation |
| big_over_25mb.csv | 26,214,401 | 413 | 0.16 | File is larger than 25 MB. | 413 | File is larger than 25 MB. | yes | 413 ok |
| big_under_25mb_wide.csv | 26,214,400 | 200 | 8.56 | amount / date | 200 | amount / date | yes | slow (P1-17) |
| bom_utf8.csv | 5,970 | 200 | 0.08 | amount / date | 200 | amount / date | yes |  |
| clean.xlsx | 6,432 | 200 | 0.11 | revenue / order_date | 200 | revenue / order_date | yes |  |
| corr_order.csv | 27,181 | 200 | 0.05 | amount / date | 200 | amount / date | yes |  |
| cp1252_euro.csv | 6,638 | 200 | 0.04 | None / date | 200 | amount / date | yes | P1-15 |
| csv_named_xlsx.xlsx | 138,927 | 400 | 0.01 | Could not read Excel file: Excel file format c | 200 | amount / date | yes | P2-08 |
| daily_70d_midweek.csv | 1,285 | 200 | 0.03 | sales / date | 200 | sales / date | yes | P1-07 |
| donations.csv | 138,927 | 200 | 0.35 | amount / date | 200 | amount / date | yes | P1-08 (Dec 2024 dropped) |
| edge_all_zero.csv | 1,572 | 200 | 0.08 | amount / date | 200 | amount / date | yes |  |
| edge_binary_garbage.csv | 5,000 | 400 | 0.01 | Could not parse CSV file: new-line character s | 400 | This doesn't look like a CSV or Excel file. | yes | P2-08 (400 cryptic) |
| edge_constant.csv | 1,572 | 200 | 0.04 | amount / date | 200 | amount / date | yes |  |
| edge_date_no_metric.csv | 1,817 | 200 | 0.06 | None / date | 200 | None / date | yes |  |
| edge_datelike_text.csv | 1,102 | 200 | 0.03 | amount / version | 200 | amount / None | yes | P1-18 version->date |
| edge_dup_cols.csv | 660 | 400 | 0.03 | Could not process file: 'DataFrame' object has | 200 | amount / date | yes | P2-09 |
| edge_empty.csv | 0 | 400 | 0.0 | The file has no rows. | 400 | The file has no rows. | yes | 400 ok |
| edge_gappy_unsorted.csv | 192 | 200 | 0.03 | amount / date | 200 | amount / date | yes | zero-filled gaps |
| edge_header_only.csv | 19 | 400 | 0.01 | The file has no rows. | 400 | The file has no rows. | yes | 400 ok |
| edge_html_page.csv | 40 | 400 | 0.0 | The file has no rows. | 400 | The file has no rows. | yes | 400 |
| edge_huge_values.csv | 532 | 200 | 0.04 | amount / date | 200 | amount / date | yes | P2-16 1e300 |
| edge_inf_values.csv | 425 | 200 | 0.02 | amount / date | 200 | amount / date | yes | P2-16 inf |
| edge_negative_metric.csv | 1,861 | 200 | 0.02 | profit / date | 200 | profit / date | yes |  |
| edge_newlines_only.csv | 3 | 400 | 0.0 | The file has no rows. | 400 | The file has no rows. | yes | 400 ok |
| edge_no_date.csv | 595 | 200 | 0.03 | qty / None | 200 | qty / None | yes |  |
| edge_no_numeric.csv | 1,545 | 200 | 0.05 | None / None | 200 | None / None | yes |  |
| edge_ragged.csv | 114 | 200 | 0.05 | amount / date | 200 | amount / date | yes |  |
| edge_reserved_cols.csv | 3,379 | 200 | 0.05 | set / date | 200 | set / date | yes | P1-21 SQL guard |
| edge_seq_id.csv | 589 | 200 | 0.04 | amount / None | 200 | amount / None | yes |  |
| edge_single_col.csv | 154 | 200 | 0.02 | amount / None | 200 | amount / None | yes |  |
| edge_single_col_text.csv | 21 | 200 | 0.03 | None / None | 200 | None / None | yes |  |
| edge_single_row.csv | 41 | 200 | 0.04 | amount / date | 200 | amount / date | yes |  |
| edge_trailing_blank.csv | 2,704 | 200 | 0.03 | sales / date | 200 | sales / date | yes | P2-12 whitespace rows |
| edge_two_rows.csv | 62 | 200 | 0.06 | amount / date | 200 | amount / date | yes | P1-11 forecast from 2 rows |
| edge_wide_300.csv | 97,295 | 200 | 0.39 | metric_0 / date | 200 | metric_0 / date | yes |  |
| edge_year_only.csv | 228 | 200 | 0.03 | amount / year | 200 | amount / year | yes | P1-19 yearly bucketed monthly |
| ends_dec30.csv | 7,238 | 200 | 0.05 | revenue / date | 200 | revenue / date | yes | P1-08 |
| epoch_seconds.csv | 4,537 | 200 | 0.03 | amount / timestamp | 200 | amount / timestamp | yes | ok |
| european.csv | 6,542 | 200 | 0.09 | betrag / datum | 200 | betrag / datum | yes | P1-02 |
| european_nothousands.csv | 6,364 | 200 | 0.06 | betrag / datum | 200 | betrag / datum | yes | P1-02 |
| excel_serial.csv | 3,332 | 200 | 0.03 | amount / date | 200 | amount / date | yes |  |
| expenses_currency.csv | 14,156 | 200 | 0.08 | amount / date | 200 | amount / date | yes | P1-03 |
| hindi_headers.csv | 8,405 | 200 | 0.06 | र_श / त_र_ख | 200 | राशि / तारीख | yes | P1-14 |
| ids_only_numeric.csv | 9,887 | 200 | 0.03 | invoice_number / None | 200 | None / None | yes | P1-12 |
| ids_plus_amount.csv | 8,741 | 200 | 0.04 | amount / order_date | 200 | amount / order_date | yes | P1-12 (dropdown) |
| inr_lakh.csv | 5,969 | 200 | 0.03 | revenue / date | 200 | revenue / date | yes |  |
| inventory.csv | 3,411 | 200 | 0.06 | unit_cost / None | 200 | qty / None | yes | P1-12 |
| latin1.csv | 5,726 | 200 | 0.07 | amount / date | 200 | amount / date | yes |  |
| legacy.xls | 608 | 400 | 0.0 | Could not read Excel file: `Import xlrd` faile | 400 | Could not read Excel file: `Import xlrd` faile | differs | P1-06 |
| merged_header.xlsx | 5,106 | 200 | 0.2 | None / None | 200 | jan / None | yes | P2-10 |
| metric_names.csv | 5,350 | 200 | 0.03 | corporate_sales / date | 200 | corporate_sales / date | yes | P1-13 |
| monthly_names.csv | 172 | 200 | 0.04 | revenue / None | 200 | revenue / None | yes | P2-14 top-8 cut |
| multi_sheet_cover_first.xlsx | 9,245 | 200 | 0.09 | None / None | 200 | sales / date | yes | P1-05 |
| multi_sheet_data_first.xlsx | 8,749 | 200 | 0.04 | sales / date | 200 | sales / date | yes | P1-05 |
| offset_table.xlsx | 5,603 | 200 | 0.13 | unnamed_4 / unnamed_2 | 200 | sales / date | yes | P1-04 |
| pct_bool_thousands.csv | 5,149 | 200 | 0.03 | revenue / date | 200 | revenue / date | yes | P2-14 True/False labels |
| starts_mid_month.csv | 6,286 | 200 | 0.04 | revenue / date | 200 | revenue / date | yes | P1-07 |
| thousands_text.csv | 5,031 | 200 | 0.03 | revenue / date | 200 | revenue / date | yes |  |
| title_rows_total.xlsx | 6,527 | 200 | 0.07 | unnamed_2 / sunrise_ngo_donations_report_2024 | 200 | amount / date | yes | P1-04 |
| total_row_literal.xlsx | 6,424 | 200 | 0.1 | amount / date | 200 | amount / date | yes | P1-04 double count |
| tz_mixed_offsets.csv | 7,898 | 400 | 0.02 | Mixed timezones detected. Pass utc=True in to_ | 200 | amount / created_at | differs | P1-16 |
| tz_utc.csv | 8,138 | 200 | 0.04 | amount / created_at | 200 | amount / created_at | yes | P1-07 |
| us_mdy_halfyear.csv | 2,726 | 200 | 0.02 | sales / date | 200 | sales / date | yes | P1-07 |
| utf16_tab.txt.csv | 11,454 | 400 | 0.01 | The file contains only empty cells. | 200 | amount / date | yes | P1-15 |
| weekday_names.csv | 354 | 200 | 0.09 | sales / None | 200 | sales / None | yes |  |
| xlsx_named_csv.csv | 6,432 | 200 | 0.06 | revenue / order_date | 200 | revenue / order_date | yes |  |
| year_month_ints.csv | 3,672 | 200 | 0.11 | month / year | 200 | visitors / year | yes | P1-12 month as metric |
| yyyymmdd_int.csv | 4,052 | 200 | 0.02 | amount / date | 200 | amount / date | yes |  |
