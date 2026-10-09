"""Builds patched/lumen/ from the READ-ONLY baseline by string replacement (each replacement is asserted), then writes qa_fixes.patch.
These patches exist to PROVE that the suggested fixes in REPORT.md work; they are not applied to the real repo."""
import pathlib, subprocess, shutil
SRC = pathlib.Path("/home/user/Anhad23mahajan/lumen"); DST = pathlib.Path("/home/user/work/qa/patched/lumen")
shutil.rmtree(DST, ignore_errors=True); DST.mkdir(parents=True)
for rel in ("app/__init__.py", "app/analytics.py", "app/llm.py", "app/main.py", "static/index.html", "requirements.txt", "Dockerfile"):
    (DST / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy(SRC / rel, DST / rel)
def sub(path, old, new, count=1):
    p = DST / path; s = p.read_text(); assert s.count(old) >= 1, f"pattern not found in {path}: {old[:70]!r}"
    p.write_text(s.replace(old, new, count))
A = "app/analytics.py"

# ---------------------------------------------------------------- header / constants
sub(A, 'import io, re, warnings, datetime\n', 'import io, re, warnings, datetime, unicodedata\n')
sub(A, 'ID_HINT = re.compile(r"(^|_)(id|uuid|guid|zip|zipcode|postal|phone|ssn|ein|code|index|num|no)(_|$)", re.I)',
       'ID_HINT = re.compile(r"(^|_)(id|uuid|guid|zip|zipcode|postal|pin|pincode|phone|mobile|contact|ssn|ein|code|index|num|number|no|invoice|ticket|ref|reference|account|acct|roll|aadhaar|pan|gst)(_|$)", re.I)\n'
       'CALENDAR_PART = re.compile(r"^(year|yr|month|mon|day|dow|weekday|week|quarter|qtr|hour|minute|fy|period)$", re.I)   # integer calendar columns are not measures\n'
       'MEAN_TOKENS = {"price", "rate", "score", "age", "temp", "temperature", "ratio", "avg", "average", "pct", "percent", "percentage", "unit"}\n'
       'COST_HINT = re.compile(r"cost|expens|spend|refund|loss|churn|debt|complaint|defect|return|waste|cancel|overdue", re.I)   # metrics where UP is bad\n'
       'UNIT = {"MS": "month", "W": "week", "D": "day", "YS": "year"}; ADJ = {"day": "daily", "week": "weekly", "month": "monthly", "year": "yearly"}\n'
       'MAX_ROWS = 200_000')

# ---------------------------------------------------------------- clean(): bool before int, timedelta/Decimal
sub(A, '    if isinstance(o, np.bool_): return bool(o)\n    if isinstance(o, (np.integer, int)): return int(o)\n',
       '    if isinstance(o, (bool, np.bool_)): return bool(o)\n    if isinstance(o, (np.integer, int)): return int(o)\n'
       '    if isinstance(o, (pd.Timedelta, datetime.timedelta)): return str(pd.Timedelta(o))\n'
       '    if o.__class__.__name__ == "Decimal": return float(o)\n')

# ---------------------------------------------------------------- read_raw_df: UTF-16, cp1252 before latin-1, Excel sheet/header/TOTAL, csv-named-xlsx
sub(A, '''def read_raw_df(raw: bytes, filename: str) -> pd.DataFrame:
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls")) or raw[:4] == b"PK\\x03\\x04" or raw[:8] == b"\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1":
        try: return pd.read_excel(io.BytesIO(raw))
        except Exception as e: raise ValueError(f"Could not read Excel file: {e}")

    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]
    text = None
    for enc in encodings:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError: pass
''', '''TOTAL_RE = re.compile(r"^\\s*(grand\\s+|sub\\s*-?\\s*)?totals?\\s*:?\\s*$", re.I)


def _promote_header(g: pd.DataFrame) -> pd.DataFrame:
    """g was read with header=None. Find the real header row (first row, within 30, that is mostly filled text) and drop trailing TOTAL rows."""
    g = g.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    ncols, hdr = g.shape[1], 0
    for i in range(min(30, len(g) - 1)):
        row = g.iloc[i]
        if row.notna().sum() >= max(2, 0.6 * ncols) and sum(isinstance(v, str) for v in row.dropna()) >= 0.8 * row.notna().sum():
            hdr = i; break
    cols = [str(v).strip() if pd.notna(v) else f"unnamed_{j}" for j, v in enumerate(g.iloc[hdr])]
    body = g.iloc[hdr + 1:].reset_index(drop=True); body.columns = cols; body = body.infer_objects()
    for _ in range(3):   # a TOTAL line at the bottom is double counting, not data
        if len(body) and any(isinstance(v, str) and TOTAL_RE.match(v) for v in body.iloc[-1].tolist()): body = body.iloc[:-1]
    return body


def _read_excel_best_sheet(raw: bytes) -> pd.DataFrame:
    xl = pd.ExcelFile(io.BytesIO(raw)); best = None
    for sheet in xl.sheet_names:
        g = xl.parse(sheet, header=None)
        score = g.dropna(how="all").dropna(axis=1, how="all").size
        if best is None or score > best[0]: best = (score, sheet, g)
    df = _promote_header(best[2]); df.attrs["sheet"] = best[1]; df.attrs["sheets"] = len(xl.sheet_names)
    return df


def read_raw_df(raw: bytes, filename: str) -> pd.DataFrame:
    name = (filename or "").lower()
    is_zip, is_ole = raw[:4] == b"PK\\x03\\x04", raw[:8] == b"\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1"
    if is_zip or is_ole:                                                                 # decide by magic bytes, not by file extension (a .xlsx that is really CSV is fine)
        try: return _read_excel_best_sheet(raw)
        except Exception as e: raise ValueError(f"Could not read Excel file: {e}")

    if raw[:2] in (b"\\xff\\xfe", b"\\xfe\\xff"): encodings = ["utf-16"]             # Excel 'Unicode Text'
    else: encodings = ["utf-8-sig", "cp1252", "latin-1"]                               # cp1252 BEFORE latin-1 (latin-1 never fails)
    text = None
    for enc in encodings:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError: pass
''')

sub(A, '''    lines = [ln for ln in text.splitlines() if ln.strip()][:20]''', '''    head = text[:4000]
    if head.startswith("%PDF") or sum(1 for ch in head if ord(ch) < 32 and ch not in "\\t\\r\\n") > 0.02 * max(len(head), 1):
        raise ValueError("This doesn't look like a CSV or Excel file.")
    lines = [ln for ln in text.splitlines() if ln.strip()][:20]''')

# ---------------------------------------------------------------- dates: dayfirst detection, cheap sample pre-check, stricter date-likeness, mixed tz
sub(A, '''def try_parse_dates(series: pd.Series, col_name: str) -> pd.Series | None:''', '''MONTHS = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
DATE_LIKE = re.compile(r"^\\s*(\\d{4}[-/.]\\d{1,2}([-/.]\\d{1,2})?|\\d{1,2}[-/.]\\d{1,2}[-/.]\\d{2,4}|\\d{1,2}[-/. ]" + MONTHS + r"[-/. ,]*\\d{2,4}|" + MONTHS + r"[-/. ]+\\d{1,2}[,-/. ]+\\d{2,4}|" + MONTHS + r"[-/. ]+\\d{2,4})", re.I)
DMY = re.compile(r"^\\s*(\\d{1,2})[-/.](\\d{1,2})[-/.]\\d{2,4}\\b")
AMBIGUOUS_DAYFIRST = True    # 03/04/2025 with nothing to disambiguate: day-first (India, EU, UK, AU...). Set False for US-only audiences.


def _to_dt(x, dayfirst=False):
    try: out = pd.to_datetime(x, format="mixed", errors="coerce", dayfirst=dayfirst)
    except ValueError: out = None                         # pandas 3 raises on mixed UTC offsets (DST!)
    if out is None or out.dtype == object:                # pandas 2.2 returns an object column instead; both: convert to UTC, drop the zone
        out = pd.to_datetime(x, format="mixed", errors="coerce", dayfirst=dayfirst, utc=True).dt.tz_localize(None)
    good = lambda o: (o.notna() & (o.dt.year > 1800)).mean()
    if good(out) < 0.5:                   # month-year labels like Jan-25 come back as year 0001 from format="mixed"
        for fmt in ("%b-%y", "%b %y", "%B-%y", "%B %y"):
            alt = pd.to_datetime(x, format=fmt, errors="coerce")
            if good(alt) > good(out): out = alt
    return out


def _detect_dayfirst(non_null: pd.Series) -> bool:
    m = non_null.str.extract(DMY)
    if m[0].notna().mean() < 0.5: return False                       # not a d/m/y text column
    a, b = pd.to_numeric(m[0], errors="coerce"), pd.to_numeric(m[1], errors="coerce")
    a_big, b_big = bool((a > 12).any()), bool((b > 12).any())
    if a_big and not b_big: return True                                # 13/01/2025 can only be day-first
    if b_big and not a_big: return False                               # 01/13/2025 can only be month-first
    if a_big and b_big: return False                                   # inconsistent column: keep pandas default
    # fully ambiguous: prefer the reading that yields the tighter span (real exports are contiguous), then the module default
    spans = []
    for dfirst in (True, False):
        p = _to_dt(non_null, dfirst).dropna()
        spans.append((p.max() - p.min()) if len(p) else pd.Timedelta.max)
    if spans[0] == spans[1]: return AMBIGUOUS_DAYFIRST
    return bool(spans[0] < spans[1])


def try_parse_dates(series: pd.Series, col_name: str) -> pd.Series | None:''')
sub(A, '''        has_separators = non_null.str.contains(r"[-/.]|[A-Za-z]{3,}").mean() > 0.7
        col_suggests_date = bool(re.search(r"(^|_)(date|dt|time|timestamp|day|month|created_at|updated_at|order_date|trans_date|invoice_date|period)(_|$)", col_name, re.I))

        if has_separators or col_suggests_date:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed = pd.to_datetime(series, format="mixed", errors="coerce")
                if parsed.dropna().shape[0] / len(non_null) > 0.75:''', '''        has_separators = non_null.str.contains(r"[-/.]|[A-Za-z]{3,}").mean() > 0.7
        col_suggests_date = bool(re.search(r"(^|_)(date|dt|time|timestamp|day|month|created_at|updated_at|order_date|trans_date|invoice_date|period)(_|$)", col_name, re.I))

        if has_separators or col_suggests_date:
            sample = non_null if len(non_null) <= 300 else non_null.sample(300, random_state=0)
            if sample.str.match(DATE_LIKE).mean() < 0.8: return None       # names / SKUs / version strings: do not even try (was 3 s per 200k-row text column)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dayfirst = _detect_dayfirst(non_null)
                parsed = _to_dt(series, dayfirst)
                if parsed.dropna().shape[0] / len(non_null) > 0.75:''')

# ---------------------------------------------------------------- numbers: symbols/words, negatives, decimal comma
sub(A, '''    def clean_num_str(s):
        return (s.astype(str).str.strip()
                .str.replace(r"^[\\$€£¥₹\\s]+", "", regex=True)
                .str.replace(r"[\\$€£¥₹\\s]+$", "", regex=True)
                .str.replace(r"^\\((.*)\\)$", r"-\\1", regex=True)
                .str.replace(r"%$", "", regex=True)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace(r"^-$", "0", regex=True))

    s_cleaned = clean_num_str(non_null)''', '''    CUR = r"(?i)(usd|eur|gbp|inr|rs\\.?|[\\$€£¥₹])"
    def strip_symbols(s):
        s = s.astype(str).str.strip().str.replace("\\u2212", "-", regex=False).str.replace(CUR, "", regex=True).str.strip()
        s = s.str.replace(r"^\\((.*)\\)$", r"-\\1", regex=True).str.replace(r"^(.*\\d)-$", r"-\\1", regex=True)          # (12) and 12-  => -12
        return s.str.replace(r"^-\\s+", "-", regex=True).str.replace("%", "", regex=False).str.replace(r"[\\s']", "", regex=True)

    def decimal_style(s):                        # "1.234,56" / "1234,56" => comma is the decimal mark
        eu = s.str.match(r"^-?\\d{1,3}(\\.\\d{3})*,\\d+$").sum() + s.str.match(r"^-?\\d+,\\d{1,2}$").sum()
        us = s.str.match(r"^-?\\d{1,3}(,\\d{3})+(\\.\\d+)?$").sum() + s.str.match(r"^-?\\d+\\.\\d+$").sum()
        return eu > us

    def clean_num_str(s, eu):
        s = strip_symbols(s)
        return s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False) if eu else s.str.replace(",", "", regex=False)

    probe = non_null if len(non_null) <= 300 else non_null.sample(300, random_state=0)      # cheap rejection of text columns before scanning every row
    if pd.to_numeric(clean_num_str(probe, decimal_style(strip_symbols(probe))), errors="coerce").notna().mean() <= 0.8: return None
    eu_style = decimal_style(strip_symbols(non_null))
    s_cleaned = clean_num_str(non_null, eu_style)''')
sub(A, '        full_cleaned = clean_num_str(series)\n', '        full_cleaned = clean_num_str(series, eu_style)\n')

# ---------------------------------------------------------------- preprocess: blank handling first, unicode-safe unique slugs, truncate BEFORE the slow work
sub(A, '''    if df.empty: raise ValueError("The file has no rows.")
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.empty: raise ValueError("The file contains only empty cells.")

    clean_cols = []
    seen = {}
    for i, c in enumerate(df.columns):
        base = re.sub(r"\\W+", "_", str(c).strip()).strip("_").lower() or f"col_{i}"
        if base in seen:
            seen[base] += 1
            clean_cols.append(f"{base}_{seen[base]}")
        else:
            seen[base] = 0
            clean_cols.append(base)
    df.columns = clean_cols
''', '''    if df.empty: raise ValueError("The file has no rows.")
    meta = dict(df.attrs)
    df = df.copy()
    for c in df.columns:      # normalise blanks FIRST so whitespace-only rows / 'N/A' columns are recognised as empty
        if pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_object_dtype(df[c]):
            df[c] = df[c].map(lambda x: x.strip() if isinstance(x, str) else x).replace(r"^\\s*$", np.nan, regex=True).replace(to_replace=NA_RE, value=np.nan)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.empty: raise ValueError("The file contains only empty cells.")
    df.attrs.update(meta)
    if len(df) > MAX_ROWS: df.attrs["truncated_from"] = len(df); df = df.head(MAX_ROWS)

    def slug(c, i):       # keep letters, digits AND combining marks (Devanagari matras, NFD accents)
        s = unicodedata.normalize("NFC", str(c)).strip()
        s = "".join(ch if (ch.isalnum() or unicodedata.category(ch)[0] == "M") else "_" for ch in s)
        return re.sub(r"_+", "_", s).strip("_").lower() or f"col_{i}"
    clean_cols, used = [], set()
    for i, c in enumerate(df.columns):
        base = slug(c, i); name, n = base, 0
        while name in used: n += 1; name = f"{base}_{n}"
        used.add(name); clean_cols.append(name)
    df.columns = clean_cols
''')
sub(A, '    return df.head(200_000)\n', '    return df\n')
sub(A, "            df[c] = bool_series\n            continue\n\n    return df\n", "            df[c] = bool_series\n            continue\n\n    num = df.select_dtypes('number').columns\n    if len(num): df[num] = df[num].replace([np.inf, -np.inf], np.nan)   # 'inf' in a CSV is a division error, not a value\n    return df\n")

# ---------------------------------------------------------------- profile: calendar parts are not metrics; sum-type metrics preferred; token-based agg_for
sub(A, '    metrics = [c["name"] for c in cols if c["kind"] == "numeric" and not c.get("id_like")]\n',
       '    metrics = [c["name"] for c in cols if c["kind"] == "numeric" and not c.get("id_like") and not CALENDAR_PART.match(c["name"])]\n')
sub(A, '''    hinted_metrics = [m for m in metrics if STRONG_HINT.search(m)] or [m for m in metrics if METRIC_HINT.search(m)]
    selected_metric = (hinted_metrics or metrics or [None])[0]''', '''    hinted_metrics = [m for m in metrics if STRONG_HINT.search(m)] or [m for m in metrics if METRIC_HINT.search(m)]
    summable = [m for m in hinted_metrics if agg_for(m) == "sum"] or [m for m in metrics if METRIC_HINT.search(m) and agg_for(m) == "sum"]
    selected_metric = (summable or hinted_metrics or metrics or [None])[0]''')
sub(A, 'def agg_for(metric): return "mean" if MEAN_HINT.search(metric) else "sum"',
       'def agg_for(metric): return "mean" if MEAN_TOKENS & set(re.split(r"[^a-z0-9]+", str(metric).lower())) else "sum"')

# ---------------------------------------------------------------- period_series: yearly freq, trim partial first/last buckets (W and MS)
sub(A, '''    span = (d[date].max() - d[date].min()).days
    freq = "MS" if span > 180 else "W" if span > 45 else "D"
    s = getattr(d.set_index(date)[metric].resample(freq), agg_for(metric))()''', '''    lo, hi = d[date].min(), d[date].max()
    span = (hi - lo).days
    freq = "YS" if (span > 365 * 2 and (d[date].dt.month == 1).all() and (d[date].dt.day == 1).all()) else "MS" if span > 180 else "W" if span > 45 else "D"
    s = getattr(d.set_index(date)[metric].resample(freq), agg_for(metric))()''')
sub(A, '''    if freq == "MS" and len(s) > 6 and d[date].max() < s.index[-1] + pd.offsets.MonthEnd(0):
        s = s.iloc[:-1]  # drop the incomplete last month so it doesn't look like a crash
    return s, freq''', '''    if freq == "MS" and len(s) > 3:       # drop a first month that starts after the 3rd and a last month that stops >2 days before month end
        if lo > s.index[0] + pd.Timedelta(days=2): s = s.iloc[1:]
        if len(s) > 3 and hi < s.index[-1] + pd.offsets.MonthEnd(0) - pd.Timedelta(days=2): s = s.iloc[:-1]
    if freq == "W" and len(s) > 3:        # bins are labelled by the week-ENDING Sunday: partial if data starts after Tue / ends before Sat
        if lo.normalize() > s.index[0].normalize() - pd.Timedelta(days=5): s = s.iloc[1:]
        if len(s) > 3 and hi.normalize() < s.index[-1].normalize() - pd.Timedelta(days=1): s = s.iloc[:-1]
    return s, freq''')
for old, new in [('unit = {"MS": "month", "W": "week", "D": "day"}[freq]', 'unit = UNIT[freq]'), ('label = {"MS": "month", "W": "week", "D": "day"}[freq]', 'label = UNIT[freq]'),
                 ('unit = {"MS": "months", "W": "weeks", "D": "days"}[freq]', 'unit = UNIT[freq] + "s"'), ('m = {"MS": 12, "W": 52, "D": 7}[freq]', 'm = {"MS": 12, "W": 52, "D": 7, "YS": 1}[freq]')]:
    sub(A, old, new, count=3)
sub(A, '"note": s.idxmax().strftime("%b %Y" if freq == "MS" else "%d %b %Y")', '"note": s.idxmax().strftime("%Y" if freq == "YS" else "%b %Y" if freq == "MS" else "week ending %d %b %Y" if freq == "W" else "%d %b %Y")')

# ---------------------------------------------------------------- insights
sub(A, '''    for c in p["columns"]:
        if c["missing_pct"] > 20:''', '''    if df.attrs.get("truncated_from"):
        f.append({"kind": "quality", "severity": "warn", "title": f"Only the first {len(df):,} of {df.attrs['truncated_from']:,} rows were analysed",
                  "detail": "Totals and trends exclude the remaining rows.", "action": "Split the file by year or filter it, then upload again."})
    if df.attrs.get("sheets", 1) > 1:
        f.append({"kind": "quality", "severity": "info", "title": f"Read sheet '{df.attrs['sheet']}' of {df.attrs['sheets']}", "detail": "Other sheets in the workbook were not analysed.", "action": "Upload other sheets separately if you need them."})
    for c in p["columns"]:
        if 20 < c["missing_pct"] < 100:''')
sub(A, '''                    up = ch > 0
                    f.append({"kind": "trend", "severity": "good" if up else "warn",''', '''                    up = ch > 0; good = up != bool(COST_HINT.search(m))
                    f.append({"kind": "trend", "severity": "good" if good else "warn",''')
sub(A, '''"detail": f"The average {unit}ly {m} in the most recent {k} {unit}s is {abs(ch):.0f}% {'higher' if up else 'lower'} than in the first {k}.",
                              "action": "Find out what changed and repeat it." if up else f"Look at which {(p['cat_cols'] or ['product'])[0]} or period dropped and act on it first."})''',
       '''"detail": f"The average {ADJ[unit]} {m} in the most recent {k} {unit}s is {abs(ch):.0f}% {'higher' if up else 'lower'} than in the first {k}.",
                              "action": "Find out what changed and repeat it." if good else f"Look at which {(p['cat_cols'] or ['product'])[0]} or period {'rose' if up else 'dropped'} and act on it first."})''')
sub(A, '''"detail": f"{m} was {val:,.0f} that {unit}, far from the typical {med:,.0f}.",''', '''"detail": f"{m} was {_n(val)} that {unit}, far from the typical {_n(med)}.",''')
sub(A, 'def insights(df, p):', '''def _n(x):
    x = float(x); return f"{x:,.0f}" if abs(x) >= 1000 else f"{x:,.1f}" if abs(x) >= 1 else f"{x:.3g}"


def insights(df, p):''')
sub(A, '''        if agg_for(m) == "sum" and len(g) >= 3 and g.sum() > 0:
            top = g.idxmax(); share = g.max() / g.sum()
            if share > 0.35:''', '''        if agg_for(m) == "sum" and len(g) >= 3 and (g >= 0).all() and g.sum() > 0:
            top = g.idxmax(); share = g.max() / g.sum()
            if share > max(0.35, 1.5 / len(g)):''')
sub(A, 'if pd.notna(r) and abs(r) > 0.5 and (best is None or abs(best[1])): best = (o, r)', 'if pd.notna(r) and abs(r) > 0.5 and (best is None or abs(r) > abs(best[1])): best = (o, r)')
sub(A, '    return sorted(f, key=lambda x: order[x["severity"]])[:8]', '    return sorted(f, key=lambda x: (x["kind"] == "quality", order[x["severity"]]))[:8]   # data-quality notes never crowd out findings')

# ---------------------------------------------------------------- forecast
sub(A, '''    s, freq = period_series(df, date, value)
    if len(s) < 8: raise ValueError("Need at least 8 time periods (days, weeks or months) to forecast.")''', '''    s, freq = period_series(df, date, value)
    observed = int((df[[date, value]].dropna().set_index(date)[value].resample(freq).count() > 0).sum())
    if len(s) < 8 or observed < 8: raise ValueError("Need at least 8 time periods with data (days, weeks or months) to forecast.")''')
sub(A, '''    sd = float(np.std(fit.resid)) if len(fit.resid) else 0.0
    h = np.sqrt(np.arange(1, periods + 1))
    lo, hi = fc.values - 1.96 * sd * h, fc.values + 1.96 * sd * h
    if s.min() >= 0: lo = np.maximum(lo, 0)
    prev = s.iloc[-periods:].sum() if agg_for(value) == "sum" else s.iloc[-periods:].mean()
    nxt = fc.sum() if agg_for(value) == "sum" else fc.mean()''', '''    sd = float(np.std(fit.resid)) if len(fit.resid) else 0.0
    try: k_par = int(len(fit.params_formatted))
    except Exception: k_par = 3
    sd *= np.sqrt(len(s) / max(len(s) - k_par, 3))          # in-sample residuals understate out-of-sample error when many parameters are fitted
    h = np.sqrt(np.arange(1, periods + 1))
    lo, hi = fc.values - 1.96 * sd * h, fc.values + 1.96 * sd * h
    if s.min() >= 0:
        fc = fc.clip(lower=0); lo = np.maximum(lo, 0); hi = np.maximum(hi, fc.values)
    kw = min(periods, len(s))                                 # compare like with like
    prev = s.iloc[-kw:].sum() if agg_for(value) == "sum" else s.iloc[-kw:].mean()
    nxt = fc.iloc[:kw].sum() if agg_for(value) == "sum" else fc.iloc[:kw].mean()''')
sub(A, '''"note": f"Over the next {periods} {unit}, {value} is expected to be about {abs(ch):.0f}% {'higher' if ch >= 0 else 'lower'} than the last {periods}. The shaded band is a 95% range; forecasts are estimates, not promises."}''',
       '''"note": f"Over the next {kw} {unit if kw != 1 else unit[:-1]}, {value} is expected to be about {abs(ch):.0f}% {'higher' if ch >= 0 else 'lower'} than the last {kw}. The shaded band is a 95% range; forecasts are estimates, not promises."}''')

# ---------------------------------------------------------------- main.py: threadpool, 404 passthrough, capped read
M = "app/main.py"
sub(M, 'import uuid, pathlib, logging, re\n', 'import uuid, pathlib, logging, re\nfrom starlette.concurrency import run_in_threadpool\n')
sub(M, '''    raw = await file.read()
    if len(raw) > MAX_BYTES: raise HTTPException(413, "File is larger than 25 MB.")
    try:
        raw_df = A.read_raw_df(raw, file.filename or "")
        raw_preview = A.df_to_preview(raw_df)
        processed_df = A.preprocess_df(raw_df)
        return start_session(processed_df, raw_preview)
    except ValueError as e: raise HTTPException(400, str(e))
    except Exception as e:
        logging.exception("Upload processing failed")
        raise HTTPException(400, f"Could not process file: {e}")''', '''    raw = await file.read(MAX_BYTES + 1)                      # never buffer more than the limit
    if len(raw) > MAX_BYTES: raise HTTPException(413, "File is larger than 25 MB.")
    return await run_in_threadpool(_process_upload, raw, file.filename or "")   # CPU-bound pandas work must not block the event loop


def _process_upload(raw, filename):
    try:
        raw_df = A.read_raw_df(raw, filename)
        raw_preview = A.df_to_preview(raw_df)
        processed_df = A.preprocess_df(raw_df)
        return start_session(processed_df, raw_preview)
    except ValueError as e: raise HTTPException(400, str(e))
    except Exception as e:
        logging.exception("Upload processing failed")
        raise HTTPException(400, f"Could not process file: {e}")''')
sub(M, '''    try: return A.clean(A.forecast(get_df(body.session_id), body.date_col, body.value_col, max(1, min(body.periods, 24))))''', '''    df = get_df(body.session_id)                              # 404 must not be rewrapped as a 400
    try: return A.clean(A.forecast(df, body.date_col, body.value_col, max(1, min(body.periods, 24))))''')
sub(M, '    if len(SESSIONS) > 50: SESSIONS.pop(next(iter(SESSIONS)))\n', '    if len(SESSIONS) > 50: SESSIONS.pop(next(iter(SESSIONS)))   # (see limits.py SessionStore for LRU+TTL)\n')

# ---------------------------------------------------------------- front-end: stale forecast, 422 text, no-metric forecast
H = "static/index.html"
sub(H, "if (!r.ok) throw new Error(j.detail || 'Something went wrong. Try again.')", "if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : 'That request was not valid. Try again.')")
sub(H, "$('#fgo').disabled = !p.date_cols.length; $('#ferr').textContent = p.date_cols.length ? '' : 'Forecasting needs a date column, and none was found.';",
       "$('#fgo').disabled = !(p.date_cols.length && p.metric_cols.length); $('#ferr').textContent = !p.date_cols.length ? 'Forecasting needs a date column, and none was found.' : (!p.metric_cols.length ? 'Forecasting needs a numeric column, and none was found.' : '');\n      try { Plotly.purge('fchart') } catch (e) { } $('#fnote').textContent = '';")
sub(H, "if (p.date_cols.length) runForecast()", "if (p.date_cols.length && p.metric_cols.length) runForecast()")
# requirements
sub("requirements.txt", "openpyxl\n", "openpyxl\nxlrd>=2.0.1\n")
out = []
for rel in ("app/analytics.py", "app/main.py", "static/index.html", "requirements.txt"):
    r = subprocess.run(["diff", "-u", "--label", "a/" + rel, "--label", "b/" + rel, str(SRC / rel), str(DST / rel)], capture_output=True, text=True); out.append(r.stdout)
pathlib.Path("/home/user/work/qa/patched/qa_fixes.patch").write_text("".join(out)); print("patch lines:", sum(x.count("\n") for x in out))
print("patched tree written to", DST)
