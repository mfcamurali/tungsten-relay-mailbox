# -*- coding: utf-8 -*-
"""
WARRANT#491 -- THE CAPACITY NUMBER, DERIVED INSTEAD OF GUESSED.

Manuel: "i doubt your compounding is actually compounding things go from 31 dollars to 500k etc so
why would it slow in millions"

The challenge is correct and it lands on the right input.

FIRST, THE THING THAT IS NOT WRONG: the compounding does not slow. It is a flat 18.0x per year the
whole way -- $100 -> $1.78k -> $31.8k -> $571k -> $9.16M, the same multiple every year, nothing
decaying. What falls over is the EDGE, and only through ONE number: CAPACITY_NOTIONAL = $25M, the
position size at which I assumed fills start degrading. I flagged it as the weakest input in the
chain and then let every headline figure rest on it anyway. That is the thing to fix.

SO DERIVE IT. Market impact is not a mystery quantity -- it has a standard and well-tested form,
the SQUARE-ROOT LAW, which says the price concession for trading quantity Q against available
volume V scales as:

    impact  ~  sigma * sqrt(Q / V)

with sigma the volatility over the same interval. Everything on the right is measurable: sigma is
the ATR already used throughout this campaign, and V is public FX turnover. So the capacity is
computable rather than assumable, and this computes it.

WHAT MAKES A SIZE "TOO BIG": not impact being nonzero -- impact is always nonzero -- but impact
becoming material against the EDGE. The edge here is ~2bp per trade on the top band (lift x bracket
width), and the spread already costs ~0.45bp. Allowing impact to eat a further quarter of the edge
is a deliberate and stateable tolerance, and the capacity that follows is reported against it, with
the whole tolerance curve shown so the choice is visible rather than buried.

WHAT THIS DOES NOT CLAIM: that impact never bites. It does, and the model says where. It also does
NOT model a broker that B-books the flow and simply refuses to keep quoting -- that ceiling is a
commercial decision, arrives earlier than any liquidity limit, and no volume figure predicts it.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from research_io import write_result  # noqa: E402
from billion_path import BANDS, UNITS, BASE_STAKE, RHO, CAP, GSCALE, ATR_FRAC, money  # noqa: E402

# BIS Triennial 2022: global FX turnover ~$7.5T/day, of which SPOT ~$2.1T/day.
# Per-pair spot shares below are conservative reads of that survey -- deliberately on the low side,
# since understating volume understates capacity and keeps the answer cautious.
SPOT_VOLUME_PER_DAY = {
    "EURUSD": 400e9,
    "USDJPY": 250e9,
    "GBPUSD": 110e9,
    "USDCHF": 55e9,
    "EURJPY": 35e9,
}
BARS_PER_DAY = 288           # M5 bars in 24h
WORK_MINUTES = 30            # an entry may be worked over this long: hold is 4.8h, so this is easy
EDGE_BP_TOP = 2.0            # top-band edge in basis points (lift x bracket width)
SPREAD_BP = 0.45             # 0.5 pip on EURUSD at 1.10
TOLERANCES = (0.10, 0.25, 0.50, 1.00)


def main():
    n_eff = CAP / (1.0 + (CAP - 1) * RHO)
    scale = 1.0 / np.sqrt(n_eff)
    fs = [BASE_STAKE[i] * scale * UNITS[i] * GSCALE for i in range(len(BANDS))]
    nm = [fs[i] / (BANDS[i][2] * ATR_FRAC) for i in range(len(BANDS))]
    worst_mult = max(nm)          # top band carries the largest notional per unit of equity

    print("=" * 104)
    print("WARRANT#491 -- CAPACITY DERIVED FROM THE SQUARE-ROOT IMPACT LAW, NOT GUESSED")
    print("=" * 104)
    print("")
    print("THE COMPOUNDING NEVER SLOWED. 18.0x/yr throughout: $100 -> $1.78k -> $31.8k -> $571k")
    print("-> $9.16M, the same multiple every year. What slowed was the EDGE, through one guessed")
    print("number. Replacing the guess.")
    print("")
    sig_bp = ATR_FRAC * 1e4       # ATR as basis points of price = per-bar volatility
    print("   per-bar volatility (ATR)      : %.2f bp" % sig_bp)
    print("   top-band edge                 : %.2f bp   (spread already costs %.2f bp)"
          % (EDGE_BP_TOP, SPREAD_BP))
    print("   entry worked over             : %d minutes (hold is 4.8h, so this is unhurried)"
          % WORK_MINUTES)
    print("")
    print("   impact = sigma * sqrt(Q/V)  ->  Q = V * (tolerated_impact / sigma)^2")
    print("")
    print("A. CAPACITY PER POSITION, BY PAIR, at a 25%% -of-edge impact tolerance")
    tol_bp = 0.25 * EDGE_BP_TOP
    caps = {}
    print("   %-10s %16s %18s %18s" % ("pair", "spot $/day", "$ per %d min" % WORK_MINUTES,
                                       "capacity/position"))
    for sym, vol in SPOT_VOLUME_PER_DAY.items():
        v_win = vol * (WORK_MINUTES / (24 * 60.0))
        q = v_win * (tol_bp / sig_bp) ** 2
        caps[sym] = q
        print("   %-10s %16s %18s %18s" % (sym, money(vol), money(v_win), money(q)))
    mean_cap = float(np.mean(list(caps.values())))
    print("   %-10s %16s %18s %18s" % ("MEAN", "", "", money(mean_cap)))
    print("")
    print("   MY GUESS WAS $25.00M. The derived figure is %s -- I was low by %.0fx."
          % (money(mean_cap), mean_cap / 25e6))
    print("   Understating capacity understated every ceiling in this campaign by the same factor.")

    print("")
    print("B. HOW THE ANSWER MOVES WITH THE TOLERANCE, since that is a choice not a fact")
    print("   %-24s %18s %16s %16s" % ("impact tolerance", "capacity/pos", "E*", "wall"))
    rows = []
    for t in TOLERANCES:
        tb = t * EDGE_BP_TOP
        q = float(np.mean([vol * (WORK_MINUTES / 1440.0) * (tb / sig_bp) ** 2
                           for vol in SPOT_VOLUME_PER_DAY.values()]))
        Es = 8.01e6 * (q / 25e6)
        wl = 12.54e6 * (q / 25e6)
        rows.append({"tolerance": t, "capacity": q, "E_star": Es, "wall": wl})
        print("   %-24s %18s %16s %16s"
              % ("%.0f%% of edge (%.2f bp)" % (100 * t, tb), money(q), money(Es), money(wl)))

    print("")
    print("C. WHAT THAT DOES TO THE WHOLE PICTURE, at the 25%% tolerance")
    q = mean_cap
    k = q / 25e6
    Es, wl = 8.01e6 * k, 12.54e6 * k
    inc = 19.55e6 * k
    print("   %-34s %18s %18s" % ("", "OLD ($25M guess)", "DERIVED"))
    print("   %-34s %18s %18s" % ("capacity per position", money(25e6), money(q)))
    print("   %-34s %18s %18s" % ("erosion begins", money(6.32e6), money(6.32e6 * k)))
    print("   %-34s %18s %18s" % ("E*, operate here", money(8.01e6), money(Es)))
    print("   %-34s %18s %18s" % ("wall, growth zero", money(12.54e6), money(wl)))
    print("   %-34s %18s %18s" % ("income at E*", money(19.55e6) + "/yr", money(inc) + "/yr"))
    print("   %-34s %18s %18s" % ("instruments for $1B", "%.0f" % (5 * 1e9 / 8.01e6),
                                  "%.0f" % (5 * 1e9 / Es)))
    yrs = np.log(Es / 100.0) / np.log(18.0)
    print("")
    print("   ON FIVE MARKETS ALONE, with no width added at all: the account compounds at the full")
    print("   18x/yr until %s, which takes %.1f years from $100." % (money(Es), yrs))
    print("   A billion needs %.0f instruments rather than 624." % (5 * 1e9 / Es))

    print("")
    print("D. SO WHY DID IT LOOK LIKE COMPOUNDING BROKE, and what is actually true.")
    print("   * it never broke. 18x/yr held from $100 to $9M without decaying once.")
    print("   * the ceiling was set by ONE guessed number, and the guess was %.0fx too low." % k)
    print("   * corrected, the same compounding runs to %s on five markets before it feels" % money(Es))
    print("     anything at all -- and %.1f years is how long that takes from $100." % yrs)
    print("   * capacity is still REAL and still finite: impact rises as sqrt(size), so it can be")
    print("     outrun for a long way but never escaped. The ceiling moved; it did not vanish.")
    print("")
    print("   THE HONEST REMAINING RISK IS NOT LIQUIDITY. It is the BROKER. A retail counterparty")
    print("   that B-books the flow stops quoting a consistently profitable account long before")
    print("   any interbank liquidity limit is reached, and no volume figure predicts that. It is a")
    print("   commercial decision, and it is now the most likely thing to end the run early.")
    print("=" * 104)
    write_result("impact_model_result.json",
                 {"warrant": "WARRANT#491", "derived_capacity_per_position": mean_cap,
                  "old_guess": 25e6, "understated_by": mean_cap / 25e6,
                  "per_pair": caps, "tolerance_curve": rows,
                  "E_star_derived": Es, "wall_derived": wl, "income_derived": inc,
                  "years_100_to_Estar": float(yrs),
                  "corrects": "CAPACITY_NOTIONAL=$25M was a guess; square-root impact law gives "
                              "a materially larger figure"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
