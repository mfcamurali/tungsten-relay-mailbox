# -*- coding: utf-8 -*-
"""
WARRANT#481 -- THE UNIFIED SYSTEM. All bands at once, each with its own bracket and its own stake.

Manuel: "we can run all the bands at the same time as one unit the algo can do top 20 15 10 5 2,
together this change our odds each with different sl tp ratios mathematically max returns min losses"

This is the architecture every earlier warrant was a component of, assembled once with every
correction this session produced:

  WARRANT#473  FULL DENSITY. Every bar on every instrument is a candidate. The 10.5 trades/day I
               reported for days was a STRIDE=7 sampling parameter, not a market limit.
  WARRANT#474  THE DEEP CHAMPION. The ranker was UNDERFIT at depth 4; depth 6 / 400 iterations made
               the band ordering monotone in all five folds. Using the base model here instead of
               the champion cost 2.2 points of win rate on the top band, which I did by accident
               once already this session and am not repeating.
  WARRANT#475  A BRACKET PER BAND. The optimal geometry MOVES with confidence -- the top band
               earns a 1:1 at a wide stop while the middle bands do better at 0.67:1. SL 6.0 ATR
               wins in every band; cost falls to 0.025 R.
  WARRANT#480  SIZING BY N_eff, NOT N. Holding portfolio risk constant means scaling the stake by
               1/sqrt(N_INDEPENDENT), and with rho = 0.077 that is N/[1+(N-1)rho], which saturates
               at 13. Using 1/sqrt(N) under-sized by 2.2x at a cap of 50 and 3.2x at 120.
  Survival     Kelly on each band's OWN Wilson lower bound at c = 0.20, derived from Manuel's
               ">=60% of capital" rule via P(ever below x) = x^(2/c-1).

WHY BANDS TOGETHER BEAT ANY SINGLE CUT, now that they can. WARRANT#471 tried this and LOST ($222 vs
$255) because the band win rates zigzagged -- there was no coherent ordering to size against, so
band-level sizing amplified noise. WARRANT#474 fixed the ordering. With a monotone ladder each band
is a real population with its own edge, its own best geometry and its own justified stake, and the
weak bands contribute at a small stake instead of either being discarded (losing their frequency) or
diluting the strong ones (losing their edge).

THE SURVIVAL RULE IS ENFORCED, NOT REPORTED. Every configuration whose realised drawdown exceeds the
40% allowance is marked and excluded from the recommendation, however good its return. The best row
inside the rule is the answer; the best row overall is shown beside it so the cost of the rule is
visible rather than hidden.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from hst_reader import read_hst, inventory  # noqa: E402
from indicator_battery import battery  # noqa: E402
from research_io import write_result  # noqa: E402

POINT_BY_DIGITS = {3: 0.001, 5: 0.00001}
SPREAD_PTS = 5
STRIDE = 1
TRAIN_STRIDE = 7
MAX_SPAN = 500
SEED = 20260905
KELLY_C = 0.20
RHO = 0.077
SURVIVAL_FLOOR = 0.60
LEVER_CAP = 12.0
CAPS = (10, 20, 30, 50, 80)
# WARRANT#482 -- Manuel: "include multiple trades at entry of the 2 and 5 percent bands".
# The two strongest bands take MORE THAN ONE unit per signal. That is not a new mechanism -- it is
# a stake multiplier on the bands whose edge justifies it, expressed the way a broker sees it.
# 3 units on the top 2%, 2 on the 2-5%, 1 everywhere else.
UNITS = {0: 3.0, 1: 2.0, 2: 1.0, 3: 1.0, 4: 1.0}
# WARRANT#483 -- but the units and the drawdown-targeting were introduced TOGETHER, so the gain
# cannot be attributed to either yet. These profiles separate them: every one is solved to the SAME
# 40% drawdown, so whatever differences survive are the units doing work and nothing else. FLAT is
# the null hypothesis -- if it matches, multi-unit entry is decoration and should not ship.
UNIT_PROFILES = (
    ("FLAT       1/1/1/1/1", {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}),
    ("MANUEL     3/2/1/1/1", {0: 3.0, 1: 2.0, 2: 1.0, 3: 1.0, 4: 1.0}),
    ("STEEP      4/3/2/1/1", {0: 4.0, 1: 3.0, 2: 2.0, 3: 1.0, 4: 1.0}),
    ("TOP-HEAVY  6/3/1/0/0", {0: 6.0, 1: 3.0, 2: 1.0, 3: 0.0, 4: 0.0}),
    ("MID-HEAVY  1/3/3/2/1", {0: 1.0, 1: 3.0, 2: 3.0, 3: 2.0, 4: 1.0}),
)
# and the global scalar is SOLVED so realised drawdown lands on the survival allowance rather than
# wherever it happens to fall. Every earlier run reported a drawdown; this one targets it.
TARGET_DD = 1.0 - SURVIVAL_FLOOR
BIG = 10 ** 9

# band -> (tp, sl), the per-band winners measured in WARRANT#475
BANDS = (
    ((0.00, 0.02), 6.0, 6.0),
    ((0.02, 0.05), 4.0, 6.0),
    ((0.05, 0.10), 4.0, 6.0),
    ((0.10, 0.15), 5.0, 6.0),
    ((0.15, 0.20), 5.0, 6.0),
)
TP_SET = sorted({b[1] for b in BANDS})
SL_SET = sorted({b[2] for b in BANDS})
REF_TP, REF_SL = 4.0, 6.0


def atr_of(h, l, c, n=14):
    pc = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    a = np.full(len(c), np.nan)
    if len(c) > n:
        cs = np.cumsum(tr); a[n:] = (cs[n:] - cs[:-n]) / n
    return a


def wilson_lower(k, n, z=1.96):
    if n == 0:
        return 0.0
    ph = k / n; d = 1 + z * z / n
    cc = ph + z * z / (2 * n); mm = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return max(0.0, (cc - mm) / d)


def kelly(p, wR, lR, fmax=0.5):
    if wR <= 0 or p <= 0 or p >= 1:
        return 0.0
    fs = np.linspace(0, fmax, 1201)
    a = 1 + fs * wR; b = 1 + fs * lR
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.where((a > 0) & (b > 0), p * np.log(np.maximum(a, 1e-12))
                     + (1 - p) * np.log(np.maximum(b, 1e-12)), -np.inf)
    return float(fs[int(np.nanargmax(g))])


def cache(h, l, c, a, ema, n, stride):
    idx, side, tix, six, atrs = [], [], [], [], []
    for i in range(80, n - 1, stride):
        ai = a[i]
        if not np.isfinite(ai) or ai <= 0:
            continue
        s = 1.0 if c[i] > ema[i] else -1.0
        hi = min(n, i + 1 + MAX_SPAN)
        H = h[i + 1:hi]; L = l[i + 1:hi]
        if len(H) < 3:
            continue
        if s > 0:
            fav = (H - c[i]) / ai; adv = (c[i] - L) / ai
        else:
            fav = (c[i] - L) / ai; adv = (H - c[i]) / ai
        cf = np.maximum.accumulate(np.maximum(fav, 0.0))
        ca = np.maximum.accumulate(np.maximum(adv, 0.0))
        ti = [int(np.searchsorted(cf, x)) if np.searchsorted(cf, x) < len(cf) else BIG for x in TP_SET]
        si = [int(np.searchsorted(ca, x)) if np.searchsorted(ca, x) < len(ca) else BIG for x in SL_SET]
        idx.append(i); side.append(s); tix.append(ti); six.append(si); atrs.append(ai)
    if not idx:
        return None
    return {"idx": np.array(idx), "side": np.array(side), "tix": np.array(tix),
            "six": np.array(six), "atr": np.array(atrs)}


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier

    inv = [r for r in inventory(min_bars=40000) if r["period"] == 5]
    raw = {}
    print("=" * 112)
    print("WARRANT#481 -- UNIFIED SYSTEM: all bands as one unit, each with its own bracket & stake")
    print("=" * 112)
    for rec in inv:
        d = read_hst(rec["path"]); n = d["n"]
        a = atr_of(d["high"], d["low"], d["close"])
        F, meta = battery(d["time"], d["open"], d["high"], d["low"], d["close"], d["volume"])
        names = sorted(F.keys())
        M = np.column_stack([F[k] for k in names]).astype(float)
        sg = np.array([bool(meta.get(k, {}).get("signed")) for k in names])
        ct = np.array([float(meta.get(k, {}).get("center", 0.0)) for k in names])
        c = d["close"]
        ema = np.empty(n); e = c[0]; kk = 2.0 / 51.0
        for i in range(n):
            e = c[i] * kk + e * (1 - kk); ema[i] = e
        tr = cache(d["high"], d["low"], c, a, ema, n, TRAIN_STRIDE)
        fl = cache(d["high"], d["low"], c, a, ema, n, STRIDE)
        if tr is None or fl is None:
            continue
        raw[rec["symbol"]] = {"M": M, "sg": sg, "ct": ct, "t": d["time"],
                              "point": POINT_BY_DIGITS.get(rec["digits"], 0.0001),
                              "train": tr, "full": fl}
        print("   %-8s %7d bars -> train %d, full %d" % (rec["symbol"], n, len(tr["idx"]), len(fl["idx"])))
    print("")

    ti_ref = TP_SET.index(REF_TP); si_ref = SL_SET.index(REF_SL)
    syms = sorted(raw.keys()); P = {}; keep = None
    for held in syms:
        Xtr, ytr = [], []
        for s in syms:
            if s == held:
                continue
            R = raw[s]; T = R["train"]
            X = R["M"][T["idx"]].copy()
            X[:, R["sg"]] = (X[:, R["sg"]] - R["ct"][R["sg"]]) * T["side"][:, None]
            live = (T["tix"][:, ti_ref] < BIG) | (T["six"][:, si_ref] < BIG)
            Xtr.append(X[live]); ytr.append((T["tix"][live, ti_ref] < T["six"][live, si_ref]).astype(int))
        Xtr = np.vstack(Xtr); ytr = np.concatenate(ytr)
        if keep is None:
            keep = np.isfinite(Xtr).mean(axis=0) > 0.5
        Xtr = Xtr[:, keep]
        m = np.isfinite(Xtr).sum(axis=1) >= int(0.8 * Xtr.shape[1])
        clf = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_depth=6,
                                             min_samples_leaf=150, l2_regularization=0.5,
                                             random_state=SEED)
        clf.fit(Xtr[m], ytr[m])
        R = raw[held]; Fl = R["full"]
        X = R["M"][Fl["idx"]].copy()
        X[:, R["sg"]] = (X[:, R["sg"]] - R["ct"][R["sg"]]) * Fl["side"][:, None]
        P[held] = clf.predict_proba(X[:, keep])[:, 1]
    print("model: WARRANT#474 DEEP champion, leave-one-instrument-out, full density")
    print("")

    # ---- assemble every band's trades onto one timeline -----------------------------------------
    ev = []
    band_stat = {}
    for bi, ((blo, bhi), tp, sl) in enumerate(BANDS):
        ti = TP_SET.index(tp); si = SL_SET.index(sl)
        wins = tot = 0
        for sym in syms:
            R = raw[sym]; Fl = R["full"]; p = P[sym]
            q_hi = np.quantile(p, 1.0 - blo); q_lo = np.quantile(p, 1.0 - bhi)
            sel = (p <= q_hi) & (p > q_lo) if blo > 0 else (p >= q_lo)
            t_ = Fl["tix"][:, ti]; s_ = Fl["six"][:, si]
            live = sel & ((t_ < BIG) | (s_ < BIG))
            for j in np.where(live)[0]:
                won = 1 if t_[j] < s_[j] else 0
                span = min(t_[j], s_[j]) + 1
                t0 = float(R["t"][int(Fl["idx"][j])])
                ev.append((t0, t0 + span * 300.0, won, Fl["atr"][j], R["point"], bi))
                wins += won; tot += 1
        band_stat[bi] = (wins, tot)
    ev.sort(key=lambda x: x[0])
    days = (ev[-1][0] - ev[0][0]) / 86400.0 * (5.0 / 7.0)

    print("EACH BAND, AT FULL DENSITY WITH ITS OWN BRACKET")
    print("   %-14s %-12s %9s %9s %9s %9s %10s %10s"
          % ("band", "bracket", "trades", "per day", "win%", "fair", "lift", "stake"))
    stakes = {}
    for bi, ((blo, bhi), tp, sl) in enumerate(BANDS):
        wins, tot = band_stat[bi]
        if tot < 200:
            stakes[bi] = 0.0; continue
        wr = wins / tot
        fair = 1.0 / (1.0 + tp / sl)
        p_lo = wilson_lower(wins, tot)
        med_atr = float(np.median([e[3] for e in ev if e[5] == bi]))
        med_pt = float(np.median([e[4] for e in ev if e[5] == bi]))
        cost = (SPREAD_PTS * med_pt) / (sl * med_atr)
        f = kelly(p_lo, tp / sl - cost, -(1.0 + cost)) * KELLY_C
        stakes[bi] = f
        print("   top %3.0f-%-6.0f%% TP%.1f/SL%-4.1f %9d %9.1f %8.1f%% %8.1f%% %+9.2f%% %9.2f%%"
              % (100 * blo, 100 * bhi, tp, sl, tot, tot / days, 100 * wr, 100 * fair,
                 100 * (wr / fair - 1.0), 100 * f))
    print("")
    print("   total signals %d = %.1f per day over ~%.0f trading days"
          % (len(ev), len(ev) / days, days))
    print("")

    print("   stake scaled 1/sqrt(N_eff), N_eff = N/[1+(N-1)*%.3f]" % RHO)
    print("   units per signal: top 2%% x%.0f, 2-5%% x%.0f, rest x1   (Manuel, WARRANT#482)"
          % (UNITS[0], UNITS[1]))
    print("   global stake scalar SOLVED per cap so realised drawdown lands on %.0f%%"
          % (100 * TARGET_DD))
    print("   %-6s %8s %9s %10s %9s %11s %9s %8s %12s %9s"
          % ("cap N", "scalar", "taken", "per day", "win%", "terminal", "CAGR", "max DD",
             "250d $100", "survives"))
    out = []

    def simulate(cap, GSCALE, UNIT):
        n_eff = cap / (1.0 + (cap - 1) * RHO)
        scale = 1.0 / np.sqrt(n_eff)
        eq = 1.0; pk = 1.0; mdd = 0.0; book = []; taken = 0; w = 0
        for e in ev:
            kb = []
            for b in book:
                if b[0] <= e[0]:
                    eq *= (1.0 + b[1] * (b[3] if b[2] else b[4]))
                    pk = max(pk, eq); mdd = max(mdd, 1.0 - eq / pk)
                else:
                    kb.append(b)
            book = kb
            if len(book) >= cap:
                continue
            (blo, bhi), tp, sl = BANDS[e[5]]
            cost = (SPREAD_PTS * e[4]) / (sl * e[3])
            wR = tp / sl - cost; lR = -(1.0 + cost)
            f = stakes.get(e[5], 0.0) * scale * UNIT.get(e[5], 1.0) * GSCALE
            if f <= 0:
                continue
            book.append((e[1], f, e[2], wR, lR)); taken += 1; w += e[2]
        for b in book:
            eq *= (1.0 + b[1] * (b[3] if b[2] else b[4]))
            pk = max(pk, eq); mdd = max(mdd, 1.0 - eq / pk)
        return eq, mdd, taken, w

    for cap in CAPS:
        # solve the global scalar so realised drawdown lands ON the allowance
        lo_g, hi_g = 0.02, 1.0
        for _ in range(14):
            mid = 0.5 * (lo_g + hi_g)
            _, _mdd, _tk, _ = simulate(cap, mid, UNITS)
            if _tk < 200:
                break
            if _mdd > TARGET_DD:
                hi_g = mid
            else:
                lo_g = mid
        g = lo_g
        eq, mdd, taken, w = simulate(cap, g, UNITS)
        if taken < 200 or mdd <= 0.0005:
            continue
        cagr = eq ** (252.0 / max(1.0, days)) - 1.0
        final = 100.0 * (1.0 + cagr)
        surv = (1.0 - mdd) >= SURVIVAL_FLOOR
        out.append({"cap": cap, "gscale": g, "taken": taken, "per_day": taken / days,
                    "win_rate": w / taken, "cagr": cagr, "max_dd": mdd,
                    "final250": final, "survives": bool(surv)})
        print("   %-6d %8.3f %9d %10.1f %8.1f%% %11.3g %9.1f%% %7.1f%% %12s %9s"
              % (cap, g, taken, taken / days, 100 * w / taken, eq, 100 * cagr, 100 * mdd,
                 "$" + format(final, ",.0f"), "yes" if surv else "NO"))
    PROF_CAP = max(r["cap"] for r in out) if out else 50
    print("")
    if out:
        ok = [r for r in out if r["survives"]]
        best_all = max(out, key=lambda r: r["final250"])
        print("BEST OVERALL      : cap %d -> %.1f/day, %+.1f%% CAGR, DD %.1f%%, 250d $%s  [%s]"
              % (best_all["cap"], best_all["per_day"], 100 * best_all["cagr"],
                 100 * best_all["max_dd"], format(best_all["final250"], ",.0f"),
                 "inside the rule" if best_all["survives"] else "BREACHES the 40% rule"))
        if ok:
            b = max(ok, key=lambda r: r["final250"])
            print("BEST INSIDE >=60%%: cap %d -> %.1f/day, %+.1f%% CAGR, DD %.1f%%, 250d $%s"
                  % (b["cap"], b["per_day"], 100 * b["cagr"], 100 * b["max_dd"],
                     format(b["final250"], ",.0f")))
            print("")
            print("   THIS IS THE ANSWER: the best configuration that actually respects the")
            print("   survival rule. Rows marked NO are shown so the cost of the rule is visible.")
        else:
            print("NOTHING stays inside the 40%% drawdown allowance. The stake must come down.")
    # ---- WARRANT#483: do the units earn their keep? all profiles at the SAME 40% drawdown --------
    print("")
    print("WARRANT#483 -- MULTI-UNIT ENTRY, ISOLATED. Every profile solved to the same 40%% drawdown,")
    print("so any difference between rows is the unit ladder alone. FLAT is the null hypothesis.")
    print("   %-22s %9s %10s %9s %11s %9s %12s" % ("unit profile", "taken", "per day", "win%",
                                                   "terminal", "CAGR", "250d $100"))
    prof_out = []
    for pname, prof in UNIT_PROFILES:
        lo_g, hi_g = 0.02, 1.2
        for _ in range(14):
            mid = 0.5 * (lo_g + hi_g)
            _, _mdd, _tk, _ = simulate(PROF_CAP, mid, prof)
            if _tk < 200:
                break
            if _mdd > TARGET_DD:
                hi_g = mid
            else:
                lo_g = mid
        eq, mdd, taken, w = simulate(PROF_CAP, lo_g, prof)
        if taken < 200:
            continue
        cagr = eq ** (252.0 / max(1.0, days)) - 1.0
        prof_out.append({"profile": pname, "taken": taken, "cagr": cagr, "max_dd": mdd,
                         "final250": 100.0 * (1.0 + cagr)})
        print("   %-22s %9d %10.1f %8.1f%% %11.3g %8.1f%% %12s"
              % (pname, taken, taken / days, 100 * w / taken, eq, 100 * cagr,
                 "$" + format(100.0 * (1.0 + cagr), ",.0f")))
    if prof_out:
        flat = prof_out[0]["final250"]
        bp = max(prof_out, key=lambda r: r["final250"])
        print("")
        if bp["profile"].startswith("FLAT"):
            print("   VERDICT: FLAT wins. Multi-unit entry does NOT earn its keep at constant risk --")
            print("   at a fixed drawdown the ladder is already priced into the per-band Kelly stakes,")
            print("   so multiplying on top just re-spends the same risk budget less evenly.")
        else:
            print("   VERDICT: %s beats FLAT by %.0f%% ($%s vs $%s at identical 40%% drawdown)."
                  % (bp["profile"].split()[0], 100 * (bp["final250"] / flat - 1.0),
                     format(bp["final250"], ",.0f"), format(flat, ",.0f")))
            print("   The concentration is real: shifting weight toward the bands with the highest")
            print("   lift buys return the risk budget was already paying for.")
    print("=" * 112)
    write_result("unified_system_result.json",
                 {"warrant": "WARRANT#481", "bands": [[list(b[0]), b[1], b[2]] for b in BANDS],
                  "stakes": {str(k): v for k, v in stakes.items()},
                  "signals_per_day": len(ev) / days, "caps": out, "unit_profiles": prof_out})
    return 0


if __name__ == "__main__":
    sys.exit(main())
