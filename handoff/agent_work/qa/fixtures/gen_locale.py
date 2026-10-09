"""Locale / encoding / date-format fixtures. Output: data/*"""
import numpy as np, pandas as pd, pathlib, unicodedata
OUT = pathlib.Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(7)
n = 240
dates = pd.date_range("2024-01-01", periods=n, freq="3D")
amt = np.round(rng.uniform(100, 9999, n), 2)

# 1. European CSV: ';' sep, decimal comma, thousands '.', dd/mm/yyyy
def eu(x): return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
pd.DataFrame({"Datum": dates.strftime("%d/%m/%Y"), "Betrag": [eu(x) for x in amt], "Kategorie": rng.choice(["Miete", "Gehalt", "Material"], n)}
             ).to_csv(OUT / "european.csv", sep=";", index=False)
# same but plain decimal comma without thousands sep
pd.DataFrame({"Datum": dates.strftime("%d/%m/%Y"), "Betrag": [f"{x:.2f}".replace(".", ",") for x in amt], "Kategorie": rng.choice(["Miete", "Gehalt", "Material"], n)}
             ).to_csv(OUT / "european_nothousands.csv", sep=";", index=False)

# 2. ambiguous dates: all dd/mm with days <=12 (03/04/2025 = 3 April or March 4?) and a day-first file where >12 days exist
d1 = pd.date_range("2025-04-01", periods=12, freq="D")   # 01/04 .. 12/04 => ambiguous
pd.DataFrame({"date": d1.strftime("%d/%m/%Y"), "sales": rng.integers(100, 200, 12)}).to_csv(OUT / "ambig_dmy_small.csv", index=False)
d2 = pd.date_range("2025-01-01", "2025-06-30", freq="D")   # dd/mm/yyyy over 6 months => days >12 appear
pd.DataFrame({"date": d2.strftime("%d/%m/%Y"), "sales": rng.integers(100, 200, len(d2))}).to_csv(OUT / "ambig_dmy_halfyear.csv", index=False)
pd.DataFrame({"date": d2.strftime("%m/%d/%Y"), "sales": rng.integers(100, 200, len(d2))}).to_csv(OUT / "us_mdy_halfyear.csv", index=False)

# 3. BOM, latin-1, cp1252 with euro, utf-16 (Excel 'Unicode Text')
base = pd.DataFrame({"Date": dates.strftime("%Y-%m-%d"), "Café": rng.choice(["Crème", "Thé", "Noël"], n), "Amount": amt})
base.to_csv(OUT / "bom_utf8.csv", index=False, encoding="utf-8-sig")
base.to_csv(OUT / "latin1.csv", index=False, encoding="latin-1")
eur = base.copy(); eur["Amount"] = ["€" + f"{x:,.2f}" for x in amt]
eur.to_csv(OUT / "cp1252_euro.csv", index=False, encoding="cp1252")
base.to_csv(OUT / "utf16_tab.txt.csv", index=False, sep="\t", encoding="utf-16")

# 4. Non-ASCII headers: Hindi + accents (NFC and NFD)
hi = pd.DataFrame({"तारीख": dates.strftime("%Y-%m-%d"), "राशि": amt, "शहर": rng.choice(["दिल्ली", "मुंबई", "पुणे"], n)})
hi.to_csv(OUT / "hindi_headers.csv", index=False, encoding="utf-8")
fr = pd.DataFrame({"Date de création": dates.strftime("%Y-%m-%d"), "Montant TTC (€)": amt, "Prénom": rng.choice(["Zoé", "Étienne", "Amélie"], n)})
fr.to_csv(OUT / "accents_nfc.csv", index=False)
fr.columns = [unicodedata.normalize("NFD", c) for c in fr.columns]
fr.to_csv(OUT / "accents_nfd.csv", index=False)

# 5. tz-aware timestamps: consistent offset, and mixed offsets (DST crossing, US Eastern)
ts = pd.date_range("2025-01-01", periods=n, freq="12h", tz="UTC")
pd.DataFrame({"created_at": ts.strftime("%Y-%m-%dT%H:%M:%S+00:00"), "amount": amt}).to_csv(OUT / "tz_utc.csv", index=False)
ts_et = pd.date_range("2025-02-01", periods=n, freq="12h", tz="America/New_York")
pd.DataFrame({"created_at": ts_et.strftime("%Y-%m-%dT%H:%M:%S%z"), "amount": amt}).to_csv(OUT / "tz_mixed_offsets.csv", index=False)

# 6. integer dates 20250131; epoch seconds; excel serial
pd.DataFrame({"date": dates.strftime("%Y%m%d").astype(int), "amount": amt}).to_csv(OUT / "yyyymmdd_int.csv", index=False)
pd.DataFrame({"timestamp": (dates.astype("int64") // 10**9 if dates.dtype == "datetime64[ns]" else dates.astype("datetime64[s]").astype("int64")), "amount": amt}).to_csv(OUT / "epoch_seconds.csv", index=False)
pd.DataFrame({"date": ((dates - pd.Timestamp("1899-12-30")).days), "amount": amt}).to_csv(OUT / "excel_serial.csv", index=False)

# 7. text numbers with thousands separators + Indian lakh grouping
pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "revenue": [f"{int(x*100):,}" for x in amt]}).to_csv(OUT / "thousands_text.csv", index=False)
def lakh(x):
    s = str(int(x)); 
    if len(s) <= 3: return s
    h, t = s[:-3], s[-3:]
    parts = []
    while len(h) > 2: parts.insert(0, h[-2:]); h = h[:-2]
    if h: parts.insert(0, h)
    return ",".join(parts + [t])
pd.DataFrame({"date": dates.strftime("%d-%m-%Y"), "revenue": ["₹" + lakh(x * 100) for x in amt]}).to_csv(OUT / "inr_lakh.csv", index=False)
print("locale ok")
