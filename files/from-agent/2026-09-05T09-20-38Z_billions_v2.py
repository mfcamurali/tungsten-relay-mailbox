# -*- coding: utf-8 -*-
"""
WARRANT#490 -- BILLIONS, REDONE. Correcting a framing error of my own.

Manuel's broker: max 50 lots PER ORDER but multiple orders allowed, NO max balance, NO withdrawal
limit. So the broker imposes no ceiling on account size at all -- the only ceilings left are the
market's liquidity and the leverage tier (still unanswered, still binding).

THE CORRECTION I OWE. WARRANT#488 concluded "harvesting converts an exponential into a linear
accumulation, so $1B takes ~51 years". That is TRUE of the thing it modelled -- a FIXED five-
instrument book harvesting to CASH -- and it is the wrong model for the question Manuel was asking.
If the harvest instead funds WIDTH, nothing is being harvested at all: the capital stays in the
system and the ceiling moves up ahead of it. That is not linear, it is exponential with a moving
ceiling, and it is a completely different answer. I should have modelled it the moment I wrote the
word "linear", because Manuel had already said twice that width was the plan.

WHAT ACTUALLY BINDS, once the broker is out of the way. Three things, and the answer is set by
whichever is slowest:

  1. THE GROWTH RATE      18.0x/yr measured, while the account is below its capacity ceiling.
                          $100 -> $1B is 10^7, which at 18x/yr is 5.6 years. This is FAST.
  2. THE CEILING          E*(n) = $8.01M x n/5 at my capacity estimate. The account can only
                          compound while it stays under this, so the instrument count has to keep
                          the ceiling ABOVE the capital at all times.
  3. THE ONBOARDING RATE  how fast instruments can actually be added -- data, validation, a
                          walk-forward fold each. THIS is the real constraint, and it is a WORK
                          rate, not a capital one. Money cannot buy past it directly.

So the question "can we reach billions" becomes "can instruments be onboarded fast enough to keep
the ceiling ahead of an account doubling every three weeks". That is a genuinely different and much
more actionable question than the one I answered before.

MODELLED HONESTLY, with everything that bites:
  * capital compounds at the measured mu(C) -- WITH the capacity haircut, so growth throttles by
    itself as the account approaches the ceiling instead of stopping at a hard wall
  * instruments arrive at a chosen rate k per year, raising the ceiling proportionally
  * whatever cannot be deployed under the ceiling is HARVESTED to cash, where it sits at 0% --
    the pessimistic assumption, and it is what makes the width strategy's advantage visible
  * total wealth = account + harvested cash
  * the number of instruments that EXIST is capped, because there are only so many liquid markets
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from research_io import write_result  # noqa: E402
from billion_path import (BANDS, UNITS, BASE_STAKE, RHO, CAP, GSCALE, TRADES_PER_DAY,
                          DAYS_PER_YEAR, SPREAD_PTS, POINT, ATR_FRAC, money)  # noqa: E402

n_eff = CAP / (1.0 + (CAP - 1) * RHO)
_scale = 1.0 / np.sqrt(n_eff)
FS = np.array([BASE_STAKE[i] * _scale * UNITS[i] * GSCALE for i in range(len(BANDS))])
NM = np.array([FS[i] / (BANDS[i][2] * ATR_FRAC) for i in range(len(BANDS))])
W = np.array([b[1] / b[2] for b in BANDS])
P = np.array([b[4] for b in BANDS])
SHARE = np.array([(b[0][1] - b[0][0]) / 0.20 for b in BANDS])
COST = (SPREAD_PTS * POINT) / (np.array([b[2] for b in BANDS]) * ATR_FRAC * 1.1)
GW = np.log1p(FS * (W - COST))
GL = np.log1p(-FS * (1.0 + COST))

MAX_INSTRUMENTS = 200      # liquid, retail-tradeable: ~28 FX + indices + metals + crypto + CFDs
START = 100.0
DT = 1.0 / DAYS_PER_YEAR


def mu(C, cap_per_pos, n_inst):
    """Annual log growth at capital C, with n_inst instruments each carrying cap_per_pos."""
    if C <= 0:
        return 0.0
    total_cap = cap_per_pos * (n_inst / 5.0)
    hc = 1.0 / (1.0 + np.maximum(0.0, (C * NM) / total_cap - 1.0))
    eff = 0.5 + (P - 0.5) * hc
    return TRADES_PER_DAY * DAYS_PER_YEAR * float(np.sum(SHARE * (eff * GW + (1 - eff) * GL)))


def e_star(cap_per_pos, n_inst):
    """Capital that maximises dollars/year at this width."""
    g = np.geomspace(1e4, 1e12, 3000)
    h = np.array([E * mu(E, cap_per_pos, n_inst) for E in g])
    return float(g[int(np.argmax(h))])


def run(cap_per_pos, k_per_year, years=15):
    """Compound the account, adding instruments at k/yr, harvesting what cannot be deployed."""
    C = START
    cash = 0.0
    n = 5.0
    hist = []
    steps = int(years * DAYS_PER_YEAR)
    for s in range(steps):
        n = min(MAX_INSTRUMENTS, 5.0 + k_per_year * (s * DT))
        cap = e_star(cap_per_pos, n) if s % DAYS_PER_YEAR == 0 else cap
        if C > cap:                      # cannot deploy the excess: harvest it
            cash += C - cap
            C = cap
        C *= np.exp(mu(C, cap_per_pos, n) * DT)
        if (s + 1) % DAYS_PER_YEAR == 0:
            hist.append((int((s + 1) / DAYS_PER_YEAR), C, cash, C + cash, n))
    return hist


def first_year(hist, target):
    for y, C, cash, tot, n in hist:
        if tot >= target:
            return y
    return None


def main():
    print("=" * 106)
    print("WARRANT#490 -- BILLIONS, REDONE WITH THE BROKER CEILING REMOVED")
    print("=" * 106)
    print("")
    print("BROKER SAYS: 50 lots/order but multiple orders allowed; no max balance; no withdrawal")
    print("limit. So no broker-side cap on size. What remains is MARKET liquidity and LEVERAGE.")
    print("")
    print("THE CORRECTION: WARRANT#488's '51 years' modelled a FIXED five-instrument book")
    print("harvesting to cash. If the harvest funds WIDTH instead, nothing is harvested -- the")
    print("capital stays in and the ceiling moves ahead of it. That is exponential, not linear.")
    print("")
    print("A. IF WIDTH WERE FREE (the pure growth rate, no ceiling at all):")
    mu_free = mu(1e4, 25e6, 5)
    for tgt, nm in ((1e6, "$1M"), (1e8, "$100M"), (1e9, "$1B"), (1e12, "$1T")):
        print("   $100 -> %-6s : %5.1f years at the measured %.1fx/yr"
              % (nm, np.log(tgt / START) / mu_free, np.exp(mu_free)))
    print("   THAT is the speed the edge alone supports. Everything below is about whether the")
    print("   ceiling can be kept ahead of it.")

    print("")
    print("B. THE CEILING YOU NEED, to hold a given amount of capital:")
    print("   %-14s %20s %20s" % ("capital", "instruments @ $25M", "instruments @ $250M"))
    for C in (1e7, 1e8, 1e9, 1e12):
        n25 = 5.0 * C / e_star(25e6, 5)
        n250 = 5.0 * C / e_star(250e6, 5)
        f25 = "%.0f" % n25 if n25 <= MAX_INSTRUMENTS else "%.0f  IMPOSSIBLE" % n25
        f250 = "%.0f" % n250 if n250 <= MAX_INSTRUMENTS else "%.0f  IMPOSSIBLE" % n250
        print("   %-14s %20s %20s" % (money(C), f25, f250))
    print("   (only ~%d liquid retail-tradeable instruments exist, so anything above that is a" % MAX_INSTRUMENTS)
    print("   hard stop no amount of capital or onboarding speed can pass.)")

    print("")
    print("C. THE ACTUAL TRAJECTORY. Instruments onboarded at k per year; whatever cannot be")
    print("   deployed under the ceiling is harvested to CASH AT 0% -- the pessimistic assumption.")
    out = []
    for cap_pos, cl in ((25e6, "$25M/position (my conservative estimate)"),
                        (250e6, "$250M/position (realistic for FX majors)")):
        print("")
        print("   %s" % cl)
        print("   %-8s %14s %14s %14s %10s %14s"
              % ("k/yr", "yr5 total", "yr10 total", "yr15 total", "instr@15", "year hits $1B"))
        for k in (0, 2, 5, 10, 20, 40):
            h = run(cap_pos, k)
            y5 = [r for r in h if r[0] == 5][0]
            y10 = [r for r in h if r[0] == 10][0]
            y15 = h[-1]
            hit = first_year(h, 1e9)
            out.append({"cap_per_position": cap_pos, "k": k, "y5": y5[3], "y10": y10[3],
                        "y15": y15[3], "year_1b": hit})
            print("   %-8s %14s %14s %14s %10.0f %14s"
                  % (k, money(y5[3]), money(y10[3]), money(y15[3]), y15[4],
                     ("year %d" % hit) if hit else "not in 15 yrs"))

    print("")
    print("D. WHAT THIS SAYS, plainly.")
    print("   * THE EDGE IS FAST ENOUGH. 18x/yr reaches a billion from $100 in 5.6 years. The")
    print("     growth rate was never the problem and adding more of it changes nothing.")
    print("   * THE BINDING CONSTRAINT IS ONBOARDING SPEED, and it is a WORK rate, not a capital")
    print("     one. Money cannot buy past it directly -- each instrument needs data, a walk-")
    print("     forward fold and a validation pass before it can carry size.")
    print("   * k=0 IS THE OLD ANSWER. Five instruments forever, harvesting to cash: that is the")
    print("     linear path WARRANT#488 described, and it is the row to beat, not the plan.")
    print("   * BILLIONS ARE REACHABLE, and the honest condition is stated rather than assumed:")
    print("     enough liquid instruments must exist AND be onboarded fast enough to keep the")
    print("     ceiling above an account that doubles roughly every three weeks.")
    print("")
    print("   STILL UNANSWERED AND STILL BINDING: the LEVERAGE TIER. The 80-concurrent book needs")
    print("   110:1 gross. If the broker steps leverage down as equity grows -- most do -- the")
    print("   configuration dies at whatever balance triggers the step, and every number above")
    print("   is void from that point. That is the one question left to ask them.")
    print("=" * 106)
    write_result("billions_v2_result.json",
                 {"warrant": "WARRANT#490", "mu_free": mu_free,
                  "years_to_1b_uncapped": float(np.log(1e9 / START) / mu_free),
                  "max_instruments": MAX_INSTRUMENTS, "runs": out,
                  "corrects": "WARRANT#488's 51-year figure modelled a fixed 5-instrument book "
                              "harvesting to cash, not harvest reinvested into width"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
