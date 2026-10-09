"""Profiling, starter charts, statistical insights and forecasting. No LLM needed here."""
import io, re, warnings, datetime, unicodedata
import numpy as np, pandas as pd

METRIC_HINT = re.compile(r"amount|sales|revenue|total|donat|expens|cost|profit|qty|quantity|units|price|balance|spend|value|volume|score|rate", re.I)
STRONG_HINT = re.compile(r"amount|revenue|sales|total|donat|expens|cost|profit|spend|volume", re.I)
MEAN_HINT = re.compile(r"price|rate|score|age|temp|ratio|avg|average|pct|percent", re.I)
ID_HINT = re.compile(r"(^|_)(id|uuid|guid|zip|zipcode|postal|pin|pincode|phone|mobile|contact|ssn|ein|code|index|num|number|no|invoice|ticket|ref|reference|account|acct|roll|aadhaar|pan|gst)(_|$)", re.I)
CALENDAR_PART = re.compile(r"^(year|yr|month|mon|day|dow|weekday|week|quarter|qtr|hour|minute|fy|period)$", re.I)   # integer calendar columns are not measures
MEAN_TOKENS = {"price", "rate", "score", "age", "temp", "temperature", "ratio", "avg", "average", "pct", "percent", "percentage", "unit"}
COST_HINT = re.compile(r"cost|expens|spend|refund|loss|churn|debt|complaint|defect|return|waste|cancel|overdue", re.I)   # metrics where UP is bad
UNIT = {"MS": "month", "W": "week", "D": "day", "YS": "year"}; ADJ = {"day": "daily", "week": "weekly", "month": "monthly", "year": "yearly"}
MAX_ROWS = 200_000
STRONG_DATE_HINT = re.compile(r"order|trans|invoice|sale|event|created|purchase|bill|payment|record|activity|checkout|revenue|entry", re.I)
DATE_HINT = re.compile(r"date|time|day|month|period|timestamp|dt", re.I)
AVOID_DATE_HINT = re.compile(r"birth|dob|born|expir|delet|cancel|valid_until", re.I)
NA_RE = re.compile(r"^(n/a|na|null|none|#n/a|<na>|-)$", re.I)


def clean(o):
    """Make anything JSON-safe (numpy types, NaN, Timestamps, pd.NA, datetime)."""
    if isinstance(o, dict): return {clean(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)): return [clean(v) for v in o]
    if isinstance(o, np.ndarray): return clean(o.tolist())
    if o is pd.NaT or o is pd.NA: return None
    if isinstance(o, (pd.Timestamp, datetime.datetime, datetime.date)):
        if pd.isna(o): return None
        return o.isoformat()
    if isinstance(o, (np.datetime64,)):
        ts = pd.Timestamp(o)
        return None if pd.isna(ts) else ts.isoformat()
    if isinstance(o, (bool, np.bool_)): return bool(o)
    if isinstance(o, (np.integer, int)): return int(o)
    if isinstance(o, (pd.Timedelta, datetime.timedelta)): return str(pd.Timedelta(o))
    if o.__class__.__name__ == "Decimal": return float(o)
    if isinstance(o, (float, np.floating)): return float(o) if np.isfinite(o) else None
    if pd.isna(o): return None
    return o


TOTAL_RE = re.compile(r"^\s*(grand\s+|sub\s*-?\s*)?totals?\s*:?\s*$", re.I)


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
    is_zip, is_ole = raw[:4] == b"PK\x03\x04", raw[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    if is_zip or is_ole:                                                                 # decide by magic bytes, not by file extension (a .xlsx that is really CSV is fine)
        try: return _read_excel_best_sheet(raw)
        except Exception as e: raise ValueError(f"Could not read Excel file: {e}")

    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"): encodings = ["utf-16"]             # Excel 'Unicode Text'
    else: encodings = ["utf-8-sig", "cp1252", "latin-1"]                               # cp1252 BEFORE latin-1 (latin-1 never fails)
    text = None
    for enc in encodings:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError: pass
    if text is None:
        raise ValueError("Could not decode file. Please ensure it is a valid CSV or Excel file.")

    head = text[:4000]
    if head.startswith("%PDF") or sum(1 for ch in head if ord(ch) < 32 and ch not in "\t\r\n") > 0.02 * max(len(head), 1):
        raise ValueError("This doesn't look like a CSV or Excel file.")
    lines = [ln for ln in text.splitlines() if ln.strip()][:20]
    if not lines: raise ValueError("The file has no rows.")

    sample = "\n".join(lines)
    sep = None
    try:
        import csv
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t", "|"])
        sep = dialect.delimiter
    except Exception:
        first_line = lines[0]
        counts = {d: first_line.count(d) for d in [",", ";", "\t", "|"]}
        best = max(counts, key=counts.get)
        sep = best if counts[best] > 0 else ","

    try: df = pd.read_csv(io.StringIO(text), sep=sep, index_col=False)
    except Exception:
        try: df = pd.read_csv(io.StringIO(text), sep=None, engine="python", index_col=False)
        except Exception as e: raise ValueError(f"Could not parse CSV file: {e}")
    return df


MONTHS = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
DATE_LIKE = re.compile(r"^\s*(\d{4}[-/.]\d{1,2}([-/.]\d{1,2})?|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}[-/. ]" + MONTHS + r"[-/. ,]*\d{2,4}|" + MONTHS + r"[-/. ]+\d{1,2}[,-/. ]+\d{2,4}|" + MONTHS + r"[-/. ]+\d{2,4})", re.I)
DMY = re.compile(r"^\s*(\d{1,2})[-/.](\d{1,2})[-/.]\d{2,4}\b")
AMBIGUOUS_DAYFIRST = True    # 03/04/2025 with nothing to disambiguate: day-first (India, EU, UK, AU...). Set False for US-only audiences.


def _to_dt(x, dayfirst=False):
    try: out = pd.to_datetime(x, format="mixed", errors="coerce", dayfirst=dayfirst)
    except ValueError:        # mixed UTC offsets (DST!): convert to UTC then drop the zone
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


def try_parse_dates(series: pd.Series, col_name: str) -> pd.Series | None:
    if pd.api.types.is_datetime64_any_dtype(series):
        if hasattr(series.dt, "tz") and series.dt.tz is not None:
            return series.dt.tz_localize(None)
        return series

    # If already an object series containing date/datetime objects
    if pd.api.types.is_object_dtype(series):
        valid_objs = series.dropna()
        if len(valid_objs) > 0 and isinstance(valid_objs.iloc[0], (datetime.date, datetime.datetime, pd.Timestamp)):
            try: return pd.to_datetime(series, errors="coerce")
            except Exception: pass

    # Numeric series (Excel serial, compact YYYYMMDD, 4-digit years, Unix timestamps)
    if pd.api.types.is_numeric_dtype(series):
        non_null = series.dropna()
        if len(non_null) == 0: return None
        # Excel serial dates (e.g. 30000 to 60000)
        if re.search(r"(^|_)(date|dt|time|timestamp|day)(_|$)", col_name, re.I):
            if non_null.between(30000, 60000).mean() > 0.8:
                try:
                    parsed = pd.to_datetime(series, unit="D", origin="1899-12-30", errors="coerce")
                    if parsed.dropna().shape[0] / len(non_null) > 0.8: return parsed
                except Exception: pass
        # Compact YYYYMMDD integers (e.g. 20230115)
        if non_null.between(19000101, 21001231).mean() > 0.8:
            try:
                parsed = pd.to_datetime(series.astype(str), format="%Y%m%d", errors="coerce")
                if parsed.dropna().shape[0] / len(non_null) > 0.8: return parsed
            except Exception: pass
        # 4-digit year integers (e.g. 2021, 2022)
        if re.search(r"(^|_)(year|yr|period|date)(_|$)", col_name, re.I):
            if non_null.between(1900, 2100).mean() > 0.8:
                try:
                    parsed = pd.to_datetime(series.astype(str) + "-01-01", format="%Y-%m-%d", errors="coerce")
                    if parsed.dropna().shape[0] / len(non_null) > 0.8: return parsed
                except Exception: pass
        # Unix timestamps (seconds or milliseconds)
        if re.search(r"(^|_)(timestamp|time|date)(_|$)", col_name, re.I):
            if non_null.between(1e9, 2.5e9).mean() > 0.8:
                try: return pd.to_datetime(series, unit="s", errors="coerce")
                except Exception: pass
            elif non_null.between(1e12, 2.5e12).mean() > 0.8:
                try: return pd.to_datetime(series, unit="ms", errors="coerce")
                except Exception: pass
        return None

    # Text / string / object / category series
    if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series) or isinstance(series.dtype, pd.CategoricalDtype):
        non_null = series.dropna().astype(str).str.strip()
        if len(non_null) == 0: return None
        if set(non_null.str.lower().unique()).issubset({"true", "false", "yes", "no", "t", "f", "y", "n"}): return None

        # 4-digit years like "2021", "2022"
        if non_null.str.match(r"^(19\d\d|20\d\d|2100)$").mean() > 0.8:
            if re.search(r"(^|_)(year|yr|date|period)(_|$)", col_name, re.I):
                return pd.to_datetime(series.astype(str) + "-01-01", format="%Y-%m-%d", errors="coerce")

        # Compact YYYYMMDD strings (e.g. "20230115")
        if non_null.str.match(r"^(19|20)\d{6}$").mean() > 0.8:
            try:
                parsed = pd.to_datetime(series.astype(str), format="%Y%m%d", errors="coerce")
                if parsed.dropna().shape[0] / len(non_null) > 0.8: return parsed
            except Exception: pass

        # General date patterns (separators like - / . or month words or column name hint)
        has_separators = non_null.str.contains(r"[-/.]|[A-Za-z]{3,}").mean() > 0.7
        col_suggests_date = bool(re.search(r"(^|_)(date|dt|time|timestamp|day|month|created_at|updated_at|order_date|trans_date|invoice_date|period)(_|$)", col_name, re.I))

        if has_separators or col_suggests_date:
            sample = non_null if len(non_null) <= 300 else non_null.sample(300, random_state=0)
            if sample.str.match(DATE_LIKE).mean() < 0.8: return None       # names / SKUs / version strings: do not even try (was 3 s per 200k-row text column)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dayfirst = _detect_dayfirst(non_null)
                parsed = _to_dt(series, dayfirst)
                if parsed.dropna().shape[0] / len(non_null) > 0.75:
                    years = parsed.dropna().dt.year
                    if (years >= 1800).all() and (years <= 2200).all():
                        if hasattr(parsed.dt, "tz") and parsed.dt.tz is not None:
                            parsed = parsed.dt.tz_localize(None)
                        return parsed
    return None


def try_parse_numeric(series: pd.Series, col_name: str) -> pd.Series | None:
    if not (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series) or isinstance(series.dtype, pd.CategoricalDtype)):
        return None
    if ID_HINT.search(col_name): return None
    non_null = series.dropna().astype(str).str.strip()
    if len(non_null) == 0: return None
    if non_null.str.match(r"^0\d{2,}").any(): return None
    if set(non_null.str.lower().unique()).issubset({"true", "false", "yes", "no", "t", "f", "y", "n"}): return None

    CUR = r"(?i)(usd|eur|gbp|inr|rs\.?|[\$€£¥₹])"
    def strip_symbols(s):
        s = s.astype(str).str.strip().str.replace("\u2212", "-", regex=False).str.replace(CUR, "", regex=True).str.strip()
        s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True).str.replace(r"^(.*\d)-$", r"-\1", regex=True)          # (12) and 12-  => -12
        return s.str.replace(r"^-\s+", "-", regex=True).str.replace("%", "", regex=False).str.replace(r"[\s']", "", regex=True)

    def decimal_style(s):                        # "1.234,56" / "1234,56" => comma is the decimal mark
        eu = s.str.match(r"^-?\d{1,3}(\.\d{3})*,\d+$").sum() + s.str.match(r"^-?\d+,\d{1,2}$").sum()
        us = s.str.match(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$").sum() + s.str.match(r"^-?\d+\.\d+$").sum()
        return eu > us

    def clean_num_str(s, eu):
        s = strip_symbols(s)
        return s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False) if eu else s.str.replace(",", "", regex=False)

    probe = non_null if len(non_null) <= 300 else non_null.sample(300, random_state=0)      # cheap rejection of text columns before scanning every row
    if pd.to_numeric(clean_num_str(probe, decimal_style(strip_symbols(probe))), errors="coerce").notna().mean() <= 0.8: return None
    eu_style = decimal_style(strip_symbols(non_null))
    s_cleaned = clean_num_str(non_null, eu_style)
    num = pd.to_numeric(s_cleaned, errors="coerce")
    valid_ratio = num.dropna().shape[0] / len(non_null)
    if valid_ratio > 0.8:
        full_cleaned = clean_num_str(series, eu_style)
        parsed = pd.to_numeric(full_cleaned, errors="coerce")
        parsed[series.isna()] = np.nan
        return parsed
    return None


def try_parse_boolean(series: pd.Series) -> pd.Series | None:
    if not (pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)): return None
    non_null = series.dropna().astype(str).str.strip().str.lower()
    if len(non_null) == 0: return None
    unique_vals = set(non_null.unique())
    bool_map = {"true": True, "false": False, "yes": True, "no": False, "y": True, "n": False, "t": True, "f": False}
    if unique_vals.issubset(set(bool_map.keys())) and len(unique_vals) > 0:
        return series.astype(str).str.strip().str.lower().map(bool_map).astype("boolean")
    return None


def preprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all preprocessing: clean column names, parse types, handle missing values."""
    if df.empty: raise ValueError("The file has no rows.")
    meta = dict(df.attrs)
    df = df.copy()
    for c in df.columns:      # normalise blanks FIRST so whitespace-only rows / 'N/A' columns are recognised as empty
        if pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_object_dtype(df[c]):
            df[c] = df[c].map(lambda x: x.strip() if isinstance(x, str) else x).replace(r"^\s*$", np.nan, regex=True).replace(to_replace=NA_RE, value=np.nan)
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

    # Drop artificial index columns exported from dataframes
    for c in list(df.columns):
        if re.match(r"^unnamed_\d+$|^index$", c) and pd.api.types.is_integer_dtype(df[c]):
            if (df[c].dropna() == np.arange(len(df[c].dropna()))).all():
                df = df.drop(columns=[c])

    # Strip whitespace & standardize missing values
    for c in df.columns:
        if pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_object_dtype(df[c]):
            df[c] = df[c].map(lambda x: x.strip() if isinstance(x, str) else x)
            df[c] = df[c].replace(r"^\s*$", np.nan, regex=True)
            df[c] = df[c].replace(to_replace=NA_RE, value=np.nan)

    # Type detection: Dates FIRST, then formatted numerics, then booleans
    for c in list(df.columns):
        date_series = try_parse_dates(df[c], c)
        if date_series is not None:
            df[c] = date_series
            continue
        num_series = try_parse_numeric(df[c], c)
        if num_series is not None:
            df[c] = num_series
            continue
        bool_series = try_parse_boolean(df[c])
        if bool_series is not None:
            df[c] = bool_series
            continue

    num = df.select_dtypes('number').columns
    if len(num): df[num] = df[num].replace([np.inf, -np.inf], np.nan)   # 'inf' in a CSV is a division error, not a value
    return df


def load_df(raw: bytes, filename: str) -> pd.DataFrame:
    """Read raw bytes into a DataFrame and preprocess it."""
    return preprocess_df(read_raw_df(raw, filename))


def df_to_preview(df: pd.DataFrame, n: int = 15) -> dict:
    """Convert a DataFrame to a JSON-safe preview dict with first n rows."""
    sample = df.head(n)
    cols = [str(c) for c in sample.columns]
    dtypes = [str(sample[c].dtype) for c in sample.columns]
    rows = []
    for _, row in sample.iterrows():
        rows.append([clean(v) if not isinstance(v, str) else v for v in row.tolist()])
    return {
        "columns": cols,
        "dtypes": dtypes,
        "rows": rows,
        "total_rows": len(df),
        "total_cols": len(df.columns)
    }


def kind(s: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(s): return "date"
    if pd.api.types.is_bool_dtype(s): return "category"
    if pd.api.types.is_numeric_dtype(s): return "numeric"
    # Fallback check for datetime objects
    valid = s.dropna()
    if len(valid) and isinstance(valid.iloc[0], (pd.Timestamp, datetime.date, datetime.datetime)):
        return "date"
    return "category" if s.nunique() <= max(30, 0.05 * len(s)) else "text"


def profile(df: pd.DataFrame) -> dict:
    cols = []
    for c in df.columns:
        s = df[c]; k = kind(s)
        missing = round(float(s.isna().mean()) * 100, 1)
        uniq = int(s.nunique())
        info = {"name": c, "kind": k, "missing_pct": missing, "unique": uniq}
        if k == "numeric":
            valid = s.dropna()
            if len(valid) > 0:
                q1, q3 = valid.quantile([.25, .75]); iqr = q3 - q1
                info["outliers"] = int(((valid < q1 - 3 * iqr) | (valid > q3 + 3 * iqr)).sum()) if iqr > 0 else 0
            else: info["outliers"] = 0
            is_id = False
            if ID_HINT.search(c):
                is_id = True
            elif not METRIC_HINT.search(c) and pd.api.types.is_integer_dtype(s) and s.is_unique and len(s) >= 10:
                diffs = s.diff().dropna()
                if (diffs == 1).all(): is_id = True
            info["id_like"] = is_id
        cols.append(info)

    dates = [c["name"] for c in cols if c["kind"] == "date"]
    metrics = [c["name"] for c in cols if c["kind"] == "numeric" and not c.get("id_like") and not CALENDAR_PART.match(c["name"])]
    cats = [c["name"] for c in cols if c["kind"] == "category" and 2 <= c["unique"] <= 30]

    hinted_metrics = [m for m in metrics if STRONG_HINT.search(m)] or [m for m in metrics if METRIC_HINT.search(m)]
    summable = [m for m in hinted_metrics if agg_for(m) == "sum"] or [m for m in metrics if METRIC_HINT.search(m) and agg_for(m) == "sum"]
    selected_metric = (summable or hinted_metrics or metrics or [None])[0]

    def date_rank(col_name):
        score = 0
        if STRONG_DATE_HINT.search(col_name): score += 10
        if DATE_HINT.search(col_name): score += 5
        if AVOID_DATE_HINT.search(col_name): score -= 10
        return score

    sorted_dates = sorted(dates, key=date_rank, reverse=True)
    selected_date = (sorted_dates or [None])[0]

    out = {"rows": len(df), "columns": cols, "date_cols": sorted_dates, "metric_cols": metrics, "cat_cols": cats,
           "metric": selected_metric, "date": selected_date}
    out["kpis"] = kpis(df, out)
    return out


def kpis(df, p):
    m, d = p["metric"], p["date"]
    out = [{"label": "Rows analysed", "value": len(df), "kind": "int"}]
    if not m: return out
    val_series = df[m].dropna()
    if val_series.empty: return out
    tot = val_series.sum() if agg_for(m) == "sum" else val_series.mean()
    out.append({"label": f"{'Total' if agg_for(m) == 'sum' else 'Average'} {m}", "value": float(tot), "kind": "num"})
    if d:
        s, freq = period_series(df, d, m); unit = UNIT[freq]
        if len(s) >= 2 and s.iloc[-2]:
            out.append({"label": f"Latest full {unit}", "value": float(s.iloc[-1]), "kind": "num",
                        "delta": float((s.iloc[-1] - s.iloc[-2]) / abs(s.iloc[-2]) * 100), "vs": f"vs previous {unit}"})
        if len(s) >= 1 and not s.empty and s.notna().any():
            out.append({"label": f"Best {unit}", "value": float(s.max()), "kind": "num", "note": s.idxmax().strftime("%Y" if freq == "YS" else "%b %Y" if freq == "MS" else "week ending %d %b %Y" if freq == "W" else "%d %b %Y")})
    return out


def agg_for(metric): return "mean" if MEAN_TOKENS & set(re.split(r"[^a-z0-9]+", str(metric).lower())) else "sum"


def period_series(df, date, metric):
    d = df[[date, metric]].dropna()
    if len(d) == 0:
        return pd.Series(dtype=float), "D"
    lo, hi = d[date].min(), d[date].max()
    span = (hi - lo).days
    freq = "YS" if (span > 365 * 2 and (d[date].dt.month == 1).all() and (d[date].dt.day == 1).all()) else "MS" if span > 180 else "W" if span > 45 else "D"
    s = getattr(d.set_index(date)[metric].resample(freq), agg_for(metric))()
    if agg_for(metric) == "sum":
        s = s.fillna(0.0)
    else:
        s = s.ffill().bfill().fillna(0.0)
    if freq == "MS" and len(s) > 3:       # drop a first month that starts after the 3rd and a last month that stops >2 days before month end
        if lo > s.index[0] + pd.Timedelta(days=2): s = s.iloc[1:]
        if len(s) > 3 and hi < s.index[-1] + pd.offsets.MonthEnd(0) - pd.Timedelta(days=2): s = s.iloc[:-1]
    if freq == "W" and len(s) > 3:        # bins are labelled by the week-ENDING Sunday: partial if data starts after Tue / ends before Sat
        if lo.normalize() > s.index[0].normalize() - pd.Timedelta(days=5): s = s.iloc[1:]
        if len(s) > 3 and hi.normalize() < s.index[-1].normalize() - pd.Timedelta(days=1): s = s.iloc[:-1]
    return s, freq


def starter_charts(df, p):
    out, m, d = [], p["metric"], p["date"]
    if not m: return out
    if d:
        s, freq = period_series(df, d, m)
        if len(s) > 1:
            label = UNIT[freq]
            out.append({"title": f"{m} by {label}", "type": "line", "freq": freq,
                        "x": [t.strftime("%Y-%m-%d") for t in s.index], "y": s.round(2).tolist()})
    for c in p["cat_cols"][:2]:
        g = getattr(df.groupby(c)[m], agg_for(m))().sort_values(ascending=False).head(8)
        if not g.empty:
            out.append({"title": f"{m} by {c}", "type": "bar", "x": [str(i) for i in g.index], "y": g.round(2).tolist()})
    return out


def suggested_questions(p):
    m, c, d = p["metric"], (p["cat_cols"] or [None])[0], p["date"]
    q = []
    if m and c: q.append(f"Which {c} brings in the most {m}?")
    if m and d: q.append(f"How did {m} change month over month?")
    if m and c and d: q.append(f"Which {c} is growing fastest?")
    return q or ["Give me a summary of this data"]


def _n(x):
    x = float(x); return f"{x:,.0f}" if abs(x) >= 1000 else f"{x:,.1f}" if abs(x) >= 1 else f"{x:.3g}"


def insights(df, p):
    """Statistical findings, each with plain-English detail and a suggested action."""
    f, m, d = [], p["metric"], p["date"]
    if df.attrs.get("truncated_from"):
        f.append({"kind": "quality", "severity": "warn", "title": f"Only the first {len(df):,} of {df.attrs['truncated_from']:,} rows were analysed",
                  "detail": "Totals and trends exclude the remaining rows.", "action": "Split the file by year or filter it, then upload again."})
    if df.attrs.get("sheets", 1) > 1:
        f.append({"kind": "quality", "severity": "info", "title": f"Read sheet '{df.attrs['sheet']}' of {df.attrs['sheets']}", "detail": "Other sheets in the workbook were not analysed.", "action": "Upload other sheets separately if you need them."})
    for c in p["columns"]:
        if 20 < c["missing_pct"] < 100:
            f.append({"kind": "quality", "severity": "warn", "title": f"{c['name']} is {c['missing_pct']}% empty",
                      "detail": f"Over a fifth of rows have no value for {c['name']}, so anything based on it may be misleading.",
                      "action": f"Fill in or remove the missing {c['name']} values before relying on results that use it."})
    if not m: return f
    if d:
        s, freq = period_series(df, d, m)
        n = len(s); unit = UNIT[freq]
        if n >= 6:
            k = max(2, n // 3); first, last = s.iloc[:k].mean(), s.iloc[-k:].mean()
            if first:
                ch = (last - first) / abs(first) * 100
                if abs(ch) >= 5:
                    up = ch > 0; good = up != bool(COST_HINT.search(m))
                    f.append({"kind": "trend", "severity": "good" if good else "warn",
                              "title": f"{m} is {'up' if up else 'down'} {abs(ch):.0f}% over the period",
                              "detail": f"The average {ADJ[unit]} {m} in the most recent {k} {unit}s is {abs(ch):.0f}% {'higher' if up else 'lower'} than in the first {k}.",
                              "action": "Find out what changed and repeat it." if good else f"Look at which {(p['cat_cols'] or ['product'])[0]} or period {'rose' if up else 'dropped'} and act on it first."})
            med = s.median(); mad = (s - med).abs().median()
            if mad > 0:
                z = 0.6745 * (s - med) / mad
                for t, v in z[abs(z) > 3.5].abs().sort_values(ascending=False).head(2).index.to_series().items():
                    val = s[v]
                    f.append({"kind": "anomaly", "severity": "warn", "title": f"Unusual {unit}: {v.strftime('%d %b %Y')}",
                              "detail": f"{m} was {_n(val)} that {unit}, far from the typical {_n(med)}.",
                              "action": "Check whether this was a real event (a campaign, a big donor) or a data-entry mistake."})
    for c in p["cat_cols"]:
        g = getattr(df.groupby(c)[m], agg_for(m))()
        if agg_for(m) == "sum" and len(g) >= 3 and (g >= 0).all() and g.sum() > 0:
            top = g.idxmax(); share = g.max() / g.sum()
            if share > max(0.35, 1.5 / len(g)):
                f.append({"kind": "driver", "severity": "info", "title": f"{top} drives {share*100:.0f}% of {m}",
                          "detail": f"Across {c}, a single value ({top}) accounts for {share*100:.0f}% of total {m}. You depend heavily on it.",
                          "action": f"Protect what makes {top} work, and test whether other {c} values can grow."})
    others = [x for x in p["metric_cols"] if x != m]
    best = None
    for o in others:
        r = df[m].corr(df[o])
        if pd.notna(r) and abs(r) > 0.5 and (best is None or abs(r) > abs(best[1])): best = (o, r)
    if best:
        f.append({"kind": "driver", "severity": "info", "title": f"{m} moves with {best[0]}",
                  "detail": f"{m} and {best[0]} are strongly {'positively' if best[1] > 0 else 'negatively'} related (correlation {best[1]:.2f}). This shows they move together, not that one causes the other.",
                  "action": f"Track {best[0]} alongside {m} and test changing it."})
    order = {"warn": 0, "good": 1, "info": 2}
    return sorted(f, key=lambda x: (x["kind"] == "quality", order[x["severity"]]))[:8]   # data-quality notes never crowd out findings


def forecast(df, date, value, periods=6):
    if date not in df or value not in df: raise ValueError("Unknown column.")
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    s, freq = period_series(df, date, value)
    observed = int((df[[date, value]].dropna().set_index(date)[value].resample(freq).count() > 0).sum())
    if len(s) < 8 or observed < 8: raise ValueError("Need at least 8 time periods with data (days, weeks or months) to forecast.")
    m = {"MS": 12, "W": 52, "D": 7, "YS": 1}[freq]
    seasonal = "add" if len(s) >= 2 * m else None
    try:
        fit = ExponentialSmoothing(s, trend="add", damped_trend=True, seasonal=seasonal, seasonal_periods=m if seasonal else None).fit()
    except Exception:
        fit = ExponentialSmoothing(s, trend="add").fit()
    fc = fit.forecast(periods)
    sd = float(np.std(fit.resid)) if len(fit.resid) else 0.0
    try: k_par = int(len(fit.params_formatted))
    except Exception: k_par = 3
    sd *= np.sqrt(len(s) / max(len(s) - k_par, 3))          # in-sample residuals understate out-of-sample error when many parameters are fitted
    h = np.sqrt(np.arange(1, periods + 1))
    lo, hi = fc.values - 1.96 * sd * h, fc.values + 1.96 * sd * h
    if s.min() >= 0:
        fc = fc.clip(lower=0); lo = np.maximum(lo, 0); hi = np.maximum(hi, fc.values)
    kw = min(periods, len(s))                                 # compare like with like
    prev = s.iloc[-kw:].sum() if agg_for(value) == "sum" else s.iloc[-kw:].mean()
    nxt = fc.iloc[:kw].sum() if agg_for(value) == "sum" else fc.iloc[:kw].mean()
    ch = (nxt - prev) / abs(prev) * 100 if prev else 0
    unit = UNIT[freq] + "s"
    fmt = lambda idx: [t.strftime("%Y-%m-%d") for t in idx]
    return {"freq": freq, "history": {"x": fmt(s.index), "y": s.round(2).tolist()},
            "forecast": {"x": fmt(fc.index), "y": fc.round(2).tolist(), "lower": np.round(lo, 2).tolist(), "upper": np.round(hi, 2).tolist()},
            "note": f"Over the next {kw} {unit if kw != 1 else unit[:-1]}, {value} is expected to be about {abs(ch):.0f}% {'higher' if ch >= 0 else 'lower'} than the last {kw}. The shaded band is a 95% range; forecasts are estimates, not promises."}


def demo_df(seed=7):
    """Synthetic shop sales with a trend, seasonality, one spike and a dominant product."""
    rng = np.random.default_rng(seed)
    prods = {"Hoodie": 900, "Tote bag": 250, "Notebook": 120, "Mug": 300, "Sticker pack": 60}
    weights = np.array([.38, .17, .2, .15, .1]); regions = ["North", "South", "Campus", "Online"]
    rows = []
    for day in pd.date_range("2024-01-01", "2025-12-31"):
        winter = 1 + .5 * np.cos((day.dayofyear - 20) / 365 * 2 * np.pi)
        n = rng.poisson(8 * winter * (1 + (day - pd.Timestamp("2024-01-01")).days / 900) * (1.3 if day.dayofweek >= 5 else 1))
        if day == pd.Timestamp("2025-03-14"): n *= 5
        for _ in range(n):
            p = rng.choice(list(prods), p=weights); q = int(rng.integers(1, 4))
            rows.append((day, p, rng.choice(regions, p=[.2, .15, .35, .3]), q, prods[p], q * prods[p]))
    return pd.DataFrame(rows, columns=["order_date", "product", "region", "quantity", "unit_price", "amount"])
