# -*- coding: utf-8 -*-
"""
WARRANT#488 -- THE CYCLE ARITHMETIC, CORRECTED. Supersedes WARRANT#487's restart table.

WARRANT#487 printed harvest rates of 107% and 112% "vs continuous". A percentage of an optimum
cannot exceed 100%, so the table was wrong, and the bug is worth naming because it is the same
shape as several others this session: I used a rate measured in one regime to describe another.

  WHAT I DID   cycle time = log(E*/base) / mu0, with mu0 the CAPACITY-FREE growth rate
  WHY IT BREAKS a cycle ending at E* spends its final stretch ABOVE the capacity threshold, where
               growth has already slowed to well under mu0. Using mu0 across the whole cycle makes
               that stretch look faster than it is, so the cycle looks shorter and the harvest rate
               comes out too high -- and worst exactly for the bases nearest E*, which is why the
               error surfaced as an impossible number rather than a plausible one.

  CORRECTLY    the account passes through a range of sizes, each with its OWN growth rate, so the
               cycle time is an INTEGRAL and not a division:

                   T(b,c) = INTEGRAL from b to c of  dE / (E * mu(E))
                   harvest rate = (c - b) / T(b,c)

That integral also settles the question WARRANT#487 was reaching for. The rate is a harmonic-style
mean of E*mu(E) across the operating range, and a mean of a set cannot exceed that set's maximum, so
NO cycling band can beat holding at the single best size. The optimum is E*, the limit of Manuel's
own idea, and now that is proved rather than observed.

The monthly figure was wrong for the same reason and is recomputed here honestly.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from research_io import write_result
from harvest_exact import mu
from billion_path import money

GRID = np.geomspace(1e3, 1.5e7, 60000)
MU = np.array([mu(E) for E in GRID])
POS = MU > 1e-9
INTEG = np.zeros_like(GRID)
d = np.diff(GRID)
rate = np.where(POS, 1.0 / (GRID * np.maximum(MU, 1e-12)), np.inf)
INTEG[1:] = np.cumsum(0.5 * (rate[1:] + rate[:-1]) * d)


def cycle_time(b, c):
    """Years to grow from b to c, integrating the size-dependent growth rate."""
    return float(np.interp(c, GRID, INTEG) - np.interp(b, GRID, INTEG))


def harvest_rate(b, c):
    t = cycle_time(b, c)
    return (c - b) / t if t > 0 and np.isfinite(t) else 0.0


def main():
    harv = GRID * MU
    i = int(np.argmax(harv))
    Estar, Hstar = float(GRID[i]), float(harv[i])
    mu0 = mu(1e4)
    wall = float(GRID[MU <= 0][0]) if (MU <= 0).any() else float("nan")

    print("=" * 104)
    print("WARRANT#488 -- CYCLE ARITHMETIC CORRECTED (supersedes WARRANT#487's restart table)")
    print("=" * 104)
    print("")
    print("   capacity-free growth : %.2fx/yr   |   E* = %s harvesting %s/yr   |   wall %s"
          % (np.exp(mu0), money(Estar), money(Hstar), money(wall)))
    print("")
    print("MANUEL'S SCHEME, WITH THE CYCLE TIME INTEGRATED PROPERLY.")
    print("   %-16s %13s %15s %16s %14s"
          % ("restart base", "cycle length", "harvest/cycle", "harvest/yr", "vs best"))
    out = []
    for base in (1e2, 1.5e4, 3.18e4, 1e5, 5e5, 1e6, 3e6, 5e6, 6.5e6, 7.2e6):
        if base >= Estar:
            continue
        t = cycle_time(base, Estar)
        r = harvest_rate(base, Estar)
        out.append({"base": base, "cycle_years": t, "per_year": r})
        mark = "  <- your $31.8k" if abs(base - 3.18e4) < 1 else ""
        print("   %-16s %10.2f yrs %15s %16s %13.0f%%%s"
              % (money(base), t, money(Estar - base), money(r) + "/yr", 100 * r / Hstar, mark))
    print("   %-16s %13s %15s %16s %13.0f%%"
          % ("(never restart)", "continuous", "as it arrives", money(Hstar) + "/yr", 100))
    print("")
    print("   Every row is now BELOW 100%%, as it must be. Your $31.8k beats $15k by %.0f%% and"
          % (100 * (out[2]["per_year"] / out[1]["per_year"] - 1)))
    print("   beats starting from $100 by %.0fx -- the direction was right all along."
          % (out[2]["per_year"] / out[0]["per_year"]))

    print("")
    print("WHAT WITHDRAWING MONTHLY ACTUALLY CAPTURES -- the realistic form of the idea.")
    print("   %-22s %15s %16s %12s" % ("withdraw", "account ranges", "harvest/yr", "of best"))
    for per, lbl in ((1 / 12.0, "monthly"), (1 / 52.0, "weekly"), (1 / 4.0, "quarterly"),
                     (1.0, "annually")):
        c = Estar
        b = Estar
        for _ in range(60):
            b = float(np.interp(np.interp(c, GRID, INTEG) - per, INTEG, GRID))
        r = harvest_rate(b, c)
        print("   %-22s %15s %16s %11.0f%%" % (lbl, money(b) + " to " + money(c),
                                               money(r) + "/yr", 100 * r / Hstar))
    print("")
    print("   MONTHLY IS THE ANSWER. It is an ordinary standing withdrawal instruction, it captures")
    print("   essentially all of the theoretical maximum, and it needs no machinery at all.")
    print("")
    print("SO, THE WHOLE THING, ON FIVE MARKETS:")
    print("   * grow $100 to %s -- median ~%.1f years at the measured rate" % (
        money(Estar), cycle_time(100.0, Estar)))
    print("   * then hold the account at %s and withdraw monthly" % money(Estar))
    print("   * that pays about %s a year, indefinitely, and does not decay" % money(Hstar))
    print("   * it is an INCOME, not a path to a billion: withdrawn money stops compounding, so")
    print("     the total accumulates in a straight line rather than a curve")
    print("   * the billion comes from WIDTH -- and %s a year is what buys it. Five markets" % money(Hstar))
    print("     fund the twenty, the twenty fund the hundred, and the ceiling rises with each.")
    print("=" * 104)
    write_result("harvest_final_result.json",
                 {"warrant": "WARRANT#488", "E_star": Estar, "harvest_per_year": Hstar,
                  "wall": wall, "mu_capacity_free": mu0, "restart_bases": out,
                  "years_100_to_Estar": cycle_time(100.0, Estar),
                  "supersedes": "WARRANT#487 restart table used mu0 across the whole cycle"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
