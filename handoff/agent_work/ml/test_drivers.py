"""pytest suite for drivers.py.  Run:  cd /home/user/work/ml && ../venv/bin/python -m pytest -q test_drivers.py

Planted-effect tests: each builds data with a known cause, then asserts the detector reports that cause and nothing else.
The 500-run false-positive study lives in bench_drivers.py (results/drivers/fp_study.json); a smaller version runs here.
"""
import json
import math
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

import drivers as D

warnings.simplefilter("ignore")
PRODUCTS = {"Hoodie": (900, 0.35), "Tote": (250, 0.20), "Notebook": (120, 0.20), "Mug": (300, 0.20), "Sticker": (60, 0.05)}
REGIONS = {"North": 0.5, "South": 0.3, "Online": 0.2}


def make_sales(seed=0, days=365, noise=0.03, start="2024-01-01", spike=None, scale_all=None, price_change=None, new_product=None):
    """Daily x product x region rows. units = base * weekday factor * (1+noise*N(0,1)); amount = units * unit_price.
    spike=(date, product, +fraction) multiplies that product's units on that day (all regions);
    scale_all=(date, factor) multiplies every product that day; price_change=(from_date, product, factor);
    new_product=(from_date, name, price, base_units)."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=days, freq="D")
    dow = np.array([1.0, 0.95, 0.9, 1.0, 1.1, 1.4, 1.3])[dates.dayofweek]
    rows = []
    prods = {k: list(v) for k, v in PRODUCTS.items()}
    for p, (price, share) in prods.items():
        for g, sg in REGIONS.items():
            units = 600 * share * sg * dow * np.clip(1 + noise * rng.standard_normal(days), 0.2, None)
            unit_price = np.full(days, float(price))
            if spike and spike[1] == p:
                units = units * np.where(dates == pd.Timestamp(spike[0]), 1 + spike[2], 1.0)
            if scale_all:
                units = units * np.where(dates == pd.Timestamp(scale_all[0]), scale_all[1], 1.0)
            if price_change and price_change[1] == p:
                unit_price = unit_price * np.where(dates >= pd.Timestamp(price_change[0]), price_change[2], 1.0)
            rows.append(pd.DataFrame({"order_date": dates, "product": p, "region": g, "quantity": units, "unit_price": unit_price,
                                      "amount": units * unit_price}))
    if new_product:
        d0, name, price, base = new_product
        for g, sg in REGIONS.items():
            units = base * sg * dow * np.clip(1 + noise * rng.standard_normal(days), 0.2, None)
            units = np.where(dates >= pd.Timestamp(d0), units, 0.0)
            keep = units > 0
            rows.append(pd.DataFrame({"order_date": dates[keep], "product": name, "region": g, "quantity": units[keep],
                                      "unit_price": float(price), "amount": units[keep] * price}))
    return pd.concat(rows, ignore_index=True)


def anomalies(df, **kw):
    return D.detect_anomalies(df, "order_date", "amount", ["product", "region"], **kw)


# ============================================================================ anomalies + attribution
@pytest.mark.parametrize("seed", range(6))
def test_big_product_spike_found_and_attributed(seed):
    day = "2024-09-12"
    df = make_sales(seed, spike=(day, "Hoodie", 0.40))     # +40% on the biggest product -> about +25% on the day's total
    out = anomalies(df)
    assert [a["evidence"]["date"] for a in out] == [day]    # the planted day and nothing else
    a = out[0]
    assert a["kind"] == "anomaly" and a["severity"] == "info"
    cause = a["evidence"]["cause"]
    assert cause["type"] == "segment" and cause["segment"] == "Hoodie" and cause["dimension"] == "product"
    top = a["evidence"]["attribution"]["top"][0]
    assert top["segment"] == "Hoodie" and top["share_of_deviation"] > 0.9
    assert "Hoodie" in a["detail"]


@pytest.mark.parametrize("seed", range(6))
def test_small_product_spike_invisible_in_total_found_by_segment_pass(seed):
    day = "2024-06-03"
    df = make_sales(seed, spike=(day, "Mug", 0.40))         # Mug is ~20% by units but only ~9% of revenue -> total moves about 3-4%
    out = anomalies(df)
    assert [a["evidence"]["date"] for a in out] == [day]
    assert out[0]["evidence"]["scope"] in ("segment", "total")
    assert "Mug" in json.dumps(out[0]["evidence"]) and "Mug" in out[0]["detail"] + out[0]["title"]


def test_attribution_sums_exactly_to_the_deviation():
    df = make_sales(1, spike=("2024-09-12", "Tote", 1.5))
    a = anomalies(df)[0]
    ev = a["evidence"]
    for dim, att in ev["attribution_all_dimensions"].items():
        assert math.isclose(att["sum_of_segment_deviations"], ev["deviation"], rel_tol=0, abs_tol=1e-6 * abs(ev["observed"]))
    assert math.isclose(ev["observed"] - ev["expected"], ev["deviation"], abs_tol=1e-9)


def test_broad_spike_is_not_blamed_on_one_product():
    df = make_sales(2, scale_all=("2024-05-20", 2.5))
    out = anomalies(df)
    assert [a["evidence"]["date"] for a in out] == ["2024-05-20"]
    assert out[0]["evidence"]["cause"]["type"] == "broad"
    assert "no single" in out[0]["detail"]


def test_drop_day_is_a_warning_with_recovery_advice():
    df = make_sales(3, scale_all=("2024-07-01", 0.2))
    out = anomalies(df)
    assert len(out) == 1 and out[0]["severity"] == "warn" and out[0]["evidence"]["deviation"] < 0
    assert "stock-out" in out[0]["action"] or "outage" in out[0]["action"]


def test_demo_data_planted_day_is_found():
    sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
    try:
        from app import analytics as A
    except Exception:
        pytest.skip("repo analytics not importable")
    df = A.demo_df()
    out = D.detect_anomalies(df, "order_date", "amount", ["product", "region"])
    assert out and out[0]["evidence"]["date"] == "2025-03-14"        # demo_df multiplies that day's orders by 5
    assert out[0]["evidence"]["cause"]["type"] == "broad"           # every product rose together
    assert out[0]["evidence"]["deviation_pct"] > 100


def test_quiet_data_with_weekly_cycle_flags_nothing():
    for seed in range(8):
        assert anomalies(make_sales(seed, noise=0.05)) == []


def test_weekly_and_monthly_resolution_do_not_crash_and_find_a_big_outlier():
    rng = np.random.default_rng(0)
    wk = pd.DataFrame({"d": pd.date_range("2023-01-02", periods=80, freq="W-MON"), "v": 1000 + rng.normal(0, 30, 80)})
    wk.loc[40, "v"] = 3000
    out = D.detect_anomalies(wk, "d", "v", [])
    assert [a["evidence"]["date"] for a in out] == [wk.loc[40, "d"].strftime("%Y-%m-%d")]
    mo = pd.DataFrame({"d": pd.date_range("2020-01-01", periods=48, freq="MS"), "v": 500 + 100 * np.sin(np.arange(48) * 2 * np.pi / 12) + rng.normal(0, 10, 48)})
    mo.loc[30, "v"] = 2000
    out = D.detect_anomalies(mo, "d", "v", [])
    assert [a["evidence"]["date"] for a in out] == [mo.loc[30, "d"].strftime("%Y-%m-%d")]


# ============================================================================ variance bridge
def test_bridge_hand_computed_price_volume_mix():
    a = pd.DataFrame({"product": ["P1", "P2"], "quantity": [100.0, 50.0], "amount": [1000.0, 1000.0]})
    b = pd.DataFrame({"product": ["P1", "P2", "P3"], "quantity": [120.0, 40.0, 10.0], "amount": [1200.0, 880.0, 300.0]})
    r = D.decompose_change(a, b, "amount", "product", qty_col="quantity", price_col="unit_price")
    assert r["delta"] == 380.0 and r["check"]["exact"]
    c = r["pvm"]["components"]
    assert math.isclose(c["volume"], 10 * 2000 / 150, rel_tol=1e-12)
    assert math.isclose(c["price"], 40 * (22 - 20), rel_tol=1e-12)
    assert math.isclose(c["mix"], 0 - 10 * 2000 / 150, rel_tol=1e-12)
    assert c["new_segments"] == 300.0 and c["lost_segments"] == 0.0
    assert r["pvm"]["check"]["exact"] and math.isclose(sum(c.values()), 380.0, abs_tol=1e-9)
    assert {x["segment"]: x["status"] for x in r["contributions"]} == {"P1": "continuing", "P2": "continuing", "P3": "new"}


@pytest.mark.parametrize("seed", range(5))
def test_bridge_contributions_always_sum_to_delta(seed):
    rng = np.random.default_rng(seed)
    n = 4000
    df = pd.DataFrame({"order_date": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 120, n), unit="D"),
                       "product": rng.choice(list("ABCDEFG"), n), "region": rng.choice(["N", "S", None], n),
                       "amount": rng.gamma(2, 50, n)})
    df.loc[df.order_date < "2024-03-01", "product"] = df.loc[df.order_date < "2024-03-01", "product"].replace("G", "A")   # G is new later
    df.loc[df.order_date >= "2024-04-01", "product"] = df.loc[df.order_date >= "2024-04-01", "product"].replace("B", "C")  # B is lost later
    b = D.variance_bridge(df, "order_date", "amount", ["product", "region"], (("2024-02-01"), ("2024-02-29")), ("2024-04-01", "2024-04-30"), mode="explicit", force=True)
    assert b is not None
    for dim, r in b["evidence"]["by_dimension"].items():
        assert r["check"]["exact"], dim
        assert math.isclose(sum(x["contribution"] for x in r["contributions"]), b["evidence"]["delta"], rel_tol=1e-9, abs_tol=1e-6)
    prod = b["evidence"]["by_dimension"]["product"]["contributions"]
    st = {x["segment"]: x["status"] for x in prod}
    assert st["G"] == "new" and st["B"] == "lost"
    # independent recomputation of one number
    a_ = df[(df.order_date >= "2024-02-01") & (df.order_date <= "2024-02-29")].groupby("product").amount.sum()
    b_ = df[(df.order_date >= "2024-04-01") & (df.order_date <= "2024-04-30")].groupby("product").amount.sum()
    ref = (b_.reindex(a_.index.union(b_.index)).fillna(0) - a_.reindex(a_.index.union(b_.index)).fillna(0))
    got = {x["segment"]: x["contribution"] for x in prod}
    for k in ref.index:
        assert math.isclose(got[k], ref[k], abs_tol=1e-6)


def test_planted_price_rise_is_attributed_to_price_not_volume():
    days = 120
    df = make_sales(5, days=days, noise=0.0, price_change=("2024-03-01", "Hoodie", 1.15))   # identical units every period, Hoodie 15% dearer from 1 Mar
    b = D.variance_bridge(df, "order_date", "amount", ["product", "region"], ("2024-02-01", "2024-02-29"), ("2024-03-01", "2024-03-31"),
                          mode="explicit", qty_col="quantity", price_col="unit_price", force=True)
    ev = b["evidence"]["by_dimension"]["product"]
    pv = ev["pvm"]
    assert b["evidence"]["price_volume_used"]
    hood = [x for x in pv["per_segment"] if x["segment"] == "Hoodie"][0]
    assert math.isclose(hood["price_a"], 900.0) and math.isclose(hood["price_b"], 1035.0)
    assert math.isclose(hood["price_effect"], hood["quantity_b"] * 135.0, rel_tol=1e-9)
    others = [x for x in pv["per_segment"] if x["segment"] != "Hoodie"]
    assert all(abs(x["price_effect"]) < 1e-6 for x in others)
    c = pv["components"]
    assert c["price"] > 0 and math.isclose(c["price"], hood["price_effect"], rel_tol=1e-9)
    assert pv["check"]["exact"] and ev["check"]["exact"]
    top = ev["contributions"][0]
    assert top["segment"] == "Hoodie"
    assert "Price vs volume" in b["detail"]


def test_new_product_launch_is_reported_as_new_with_exact_value():
    df = make_sales(6, days=150, noise=0.01, new_product=("2024-03-01", "Poster", 40.0, 150.0))
    b = D.variance_bridge(df, "order_date", "amount", ["product"], ("2024-02-01", "2024-02-29"), ("2024-03-01", "2024-03-31"), mode="explicit", force=True)
    prod = b["evidence"]["by_dimension"]["product"]["contributions"]
    new = [x for x in prod if x["segment"] == "Poster"][0]
    ref = df[(df["product"] == "Poster") & (df.order_date >= "2024-03-01") & (df.order_date <= "2024-03-31")].amount.sum()
    assert new["status"] == "new" and math.isclose(new["contribution"], ref, rel_tol=1e-9) and new["a"] == 0
    assert "(new)" in b["detail"] or "Poster" in b["detail"]
    c = b["evidence"]["by_dimension"]["product"]["pvm"]["components"]
    assert math.isclose(c["new_segments"], ref, rel_tol=1e-9)


def test_bridge_stays_quiet_when_nothing_changed_and_speaks_when_it_did():
    quiet = make_sales(7, days=400, noise=0.03)
    assert D.variance_bridge(quiet, "order_date", "amount", ["product", "region"]) is None
    changed = make_sales(7, days=400, noise=0.03, scale_all=None, price_change=("2024-11-01", "Hoodie", 0.6))
    b = D.variance_bridge(changed, "order_date", "amount", ["product", "region"], qty_col="quantity", price_col="unit_price")
    assert b is not None and b["severity"] == "warn" and b["evidence"]["best_dimension"] == "product"
    assert b["evidence"]["by_dimension"]["product"]["contributions"][0]["segment"] == "Hoodie"


def test_bridge_modes_and_incomplete_month_handling():
    df = make_sales(8, days=200, noise=0.03)           # ends 2024-07-18: July is incomplete
    b = D.variance_bridge(df, "order_date", "amount", ["product"], force=True)
    assert b["evidence"]["period_b"]["label"] == "Jun 2024" and b["evidence"]["period_a"]["label"] == "May 2024"
    assert "incomplete" in (b["evidence"]["note"] or "")
    t = D.variance_bridge(df, "order_date", "amount", ["product"], mode="thirds", force=True)
    assert t["evidence"]["period_a"]["days"] == t["evidence"]["period_b"]["days"] == 66


def test_mean_metric_bridge_is_exact():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"order_date": pd.date_range("2024-01-01", periods=120, freq="D").repeat(5), "region": np.tile(list("ABCDE"), 120)})
    df["avg_price"] = rng.normal(50, 5, len(df)) + (df.order_date >= "2024-03-01") * (df.region == "A") * 20
    r = D.decompose_change(df[df.order_date < "2024-03-01"], df[df.order_date >= "2024-03-01"], "avg_price", "region")
    assert r["agg"] == "mean" and r["check"]["exact"]
    assert r["contributions"][0]["segment"] == "A"
    assert math.isclose(r["delta"], df[df.order_date >= "2024-03-01"].avg_price.mean() - df[df.order_date < "2024-03-01"].avg_price.mean(), rel_tol=1e-12)


# ============================================================================ change points
def level_series(seed, n=365, shift_at=200, shift=0.3, noise=0.05, weekly=True, trend=0.0):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    dow = np.array([1.0, 0.95, 0.9, 1.0, 1.1, 1.4, 1.3])[(t) % 7] if weekly else 1.0
    lvl = 1000 * (1 + trend * t) * np.where(t >= shift_at, 1 + shift, 1.0)
    return pd.Series(lvl * dow * (1 + noise * rng.standard_normal(n)), index=pd.date_range("2024-01-01", periods=n, freq="D"))


@pytest.mark.parametrize("seed,shift", [(0, 0.3), (1, -0.25), (2, 0.4), (3, -0.35), (4, 0.2)])
def test_planted_level_shift_is_located(seed, shift):
    s = level_series(seed, shift=shift)
    cps = D.detect_change_points(s, season=7, min_seg=14)
    assert len(cps) == 1
    assert abs(cps[0]["index"] - 200) <= 3
    assert abs(cps[0]["change_pct"] - shift * 100) <= 4
    assert cps[0]["t_stat"] > cps[0]["critical_value"]


def test_two_shifts_found():
    s = level_series(0, shift_at=120, shift=0.4)
    s2 = s.copy()
    s2.iloc[260:] *= 0.6
    cps = D.detect_change_points(s2, season=7, min_seg=14)
    assert [abs(c["index"] - e) <= 3 for c, e in zip(cps, (120, 260))] == [True, True] and len(cps) == 2


def test_smooth_trend_and_noise_are_not_change_points():
    assert D.detect_change_points(level_series(0, shift=0.0, trend=0.002), season=7, min_seg=14) == []      # +73% drift over the year, no step
    fp = sum(len(D.detect_change_points(level_series(s, shift=0.0), season=7, min_seg=14)) > 0 for s in range(60))
    assert fp <= 2, fp


def test_ar1_noise_does_not_hallucinate_steps():
    fp = 0
    for s in range(60):
        rng = np.random.default_rng(100 + s)
        e = np.zeros(300)
        for k in range(1, 300):
            e[k] = 0.6 * e[k - 1] + rng.normal()
        fp += len(D.detect_change_points(pd.Series(100 + 3 * e, index=pd.date_range("2024-01-01", periods=300, freq="D")), min_seg=14)) > 0
    assert fp <= 4, fp


def test_changepoint_finding_names_the_driving_segment():
    df = make_sales(9, days=365, noise=0.02, price_change=("2024-07-01", "Hoodie", 0.7))
    out = D.analyze(df, "order_date", "amount", ["product", "region"], qty_col="quantity", price_col="unit_price")
    cp = [i for i in out if i["kind"] == "changepoint"]
    assert cp and cp[0]["severity"] == "warn"
    assert abs(pd.Timestamp(cp[0]["evidence"]["date"]) - pd.Timestamp("2024-07-01")).days <= 3
    assert cp[0]["evidence"]["top_segment"]["segment"] == "Hoodie"


# ============================================================================ concentration + entities
def test_concentration_numbers_are_exact():
    df = pd.DataFrame({"seg": ["a"] * 6 + ["b"] * 3 + ["c"] + ["d"], "amount": [10.0] * 6 + [10.0] * 3 + [10.0, 10.0]})
    # shares: a=60/110.. compute exactly
    out = D.concentration(df, "amount", ["seg"], top1_flag=0.4)
    tot = 110.0
    sh = np.array([60, 30, 10, 10]) / tot
    ev = out[0]["evidence"]
    assert math.isclose(ev["hhi"], float((sh ** 2).sum())) and math.isclose(ev["top1_share"], 60 / tot) and ev["top1"] == "a"
    assert math.isclose(ev["top3_share"], 100 / tot) and out[0]["kind"] == "concentration"


def test_entity_metrics_match_hand_counts():
    rows = []
    d0 = pd.Timestamp("2024-01-05")
    for i in range(100):
        rows.append((f"D{i:03d}", d0 + pd.Timedelta(days=i % 20), 50.0))
        if i < 40:                                       # 40 donors give a second gift two months later
            rows.append((f"D{i:03d}", d0 + pd.Timedelta(days=70 + i % 20), 50.0))
    for i in range(10):                                  # 10 donors are still giving in the last window
        rows.append((f"D{i:03d}", pd.Timestamp("2024-07-10") + pd.Timedelta(days=i), 80.0))
    df = pd.DataFrame(rows, columns=["donor_id", "gift_date", "amount"])
    assert D.infer_roles(df)["entity_col"] == "donor_id"
    out = D.entity_metrics(df, "donor_id", "gift_date", "amount")
    assert len(out) == 1
    ev = out[0]["evidence"]
    assert ev["entities"] == 100 and math.isclose(ev["repeat_rate"], 0.40)      # exactly 40 donors have 2+ gift days (the 10 late ones are among them)
    assert ev["lapsed"] <= ev["prior_active"] and 0 <= ev["churn_proxy"] <= 1
    assert math.isclose(ev["churn_proxy"], ev["lapsed"] / ev["prior_active"])


# ============================================================================ contract: schema, JSON, robustness
def test_every_finding_has_the_contract_and_is_json_safe():
    df = make_sales(1, days=365, noise=0.02, spike=("2024-09-12", "Hoodie", 0.4), price_change=("2024-07-01", "Tote", 1.2))
    df["donor_id"] = np.random.default_rng(0).integers(0, 80, len(df))
    out = D.analyze(df, "order_date", "amount", ["product", "region"])
    assert out
    for it in out:
        assert set(it) == {"kind", "severity", "title", "detail", "action", "evidence"}
        assert it["severity"] in ("warn", "good", "info")
        assert it["kind"] in ("anomaly", "bridge", "changepoint", "concentration", "retention")
        assert all(isinstance(it[k], str) and it[k] for k in ("title", "detail", "action"))
        json.dumps(it)                                                           # evidence must serialise as-is


def test_numbers_in_detail_come_from_evidence():
    df = make_sales(2, spike=("2024-09-12", "Hoodie", 0.4))
    a = anomalies(df)[0]
    ev = a["evidence"]
    assert D._num(ev["observed"]) in a["detail"] and D._num(ev["expected"]) in a["detail"]
    b = D.variance_bridge(make_sales(3, days=400), "order_date", "amount", ["product"], force=True)
    top = b["evidence"]["by_dimension"]["product"]["contributions"][0]
    assert D._num(top["contribution"]) in b["detail"]
    assert D._num(b["evidence"]["total_a"]) in b["detail"] and D._num(b["evidence"]["total_b"]) in b["detail"]


def test_never_raises_on_junk():
    junk = [pd.DataFrame(), pd.DataFrame({"d": [], "v": []}), pd.DataFrame({"d": ["x", "y"], "v": [1, 2]}), pd.DataFrame({"d": pd.date_range("2024-01-01", periods=3), "v": [np.nan] * 3}),
            pd.DataFrame({"d": pd.date_range("2024-01-01", periods=50), "v": ["a"] * 50, "c": [None] * 50})]
    for df in junk:
        for fn in (lambda x: D.analyze(x, "d", "v", ["c"]), lambda x: D.detect_anomalies(x, "d", "v", ["c"]), lambda x: D.variance_bridge(x, "d", "v", ["c"]),
                   lambda x: D.concentration(x, "v", ["c"]), lambda x: D.entity_metrics(x, "c", "d", "v")):
            fn(df)
    assert D.analyze(pd.DataFrame({"a": [1]}), None, None) == []
    # constant series, a single row, int category codes, NaN categories, negative metric
    c = pd.DataFrame({"d": pd.date_range("2024-01-01", periods=90), "v": 5.0, "k": np.arange(90) % 3})
    D.analyze(c, "d", "v", ["k"])
    n = c.assign(v=-np.abs(np.random.default_rng(0).normal(10, 3, 90)), k=lambda x: x.k.where(x.k != 1))
    D.analyze(n, "d", "v", ["k"])


def test_false_positive_rate_on_pure_noise_small_study():
    res = D.false_positive_study(runs=25, days=300, seed=11)
    for kind, r in res.items():
        assert r["anomaly_runs"] <= 2, (kind, r)          # <= 8% of runs flag anything at all (full 500-run study: bench_drivers.py)
        assert r["changepoint_runs"] <= 2, (kind, r)
        assert r["bridge_runs"] <= 3, (kind, r)
