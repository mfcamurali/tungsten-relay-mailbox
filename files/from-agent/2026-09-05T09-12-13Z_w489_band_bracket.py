# -*- coding: utf-8 -*-
"""
WARRANT#489 -- BAND-CONDITIONAL BRACKETS IN THE BUILD.

WARRANT#475 and #481 measured the same thing twice: the optimal TP:SL ratio MOVES with confidence.
1.00 at the top 2%, 0.67 through the middle, 0.83 at the edge. A single global ratio is wrong for
every band at once, and the build currently has exactly one -- keyed to REGIME, never to confidence.

WHAT IS SHIPPED, and equally important, what is NOT.

SHIPPED: the STRUCTURE. A self-calibrating confidence band derived from the build's own score
margin, and a TP:SL ratio that varies across those bands. The band edges are running quantiles of
the margins the build ACTUALLY produces, so the bands mean the same thing (top 2%, top 2-5%, ...)
regardless of how the score is scaled -- which matters because the score space has moved twice
already this campaign, and any fixed margin threshold would silently mean something different after
the next recalibration.

NOT SHIPPED: the research's literal SL of 6.0 ATR. That number was measured against the RESEARCH
entry rule (EMA-50 side plus the gradient-boosted ranker), and the build enters on unifiedScore --
a different rule. WARRANT#458's finding was precisely that a bracket is NOT neutral conditional on
the entry, so a bracket optimal for one entry rule does not transfer to another by assertion. What
IS shipped is enough headroom for the build to FIND its own optimum: MAX_SL_DISTANCE_ATR was 2.8,
which clamps the research's answer out of reach before it can be tested. That clamp is the reason
the question could never have been settled inside the build, and it is what actually changes here.

The ratios enter as PRIORS with the shape the research established, and calibration moves them.
That is the honest transfer: the structure is measured and general, the magnitudes are local.

WHY QUANTILES AND NOT THRESHOLDS: the recurring defect this campaign keeps finding is a gate that
reads a rate with no sample behind it. So the band collapses to "no band" until BAND_MIN_SAMPLE
margins have been observed -- no sample means no band, not a confident band, and until then the
build behaves exactly as it does today.
"""
import io
import sys

BUILD = (r"C:\Users\User\Desktop\Work\# EX MACHINA\focus\x_strategies ix"
         r"\TUNGSTEN_10.66_APEX_QUANT_SLS(181).mq4")

OLD_CLAMP = "#define MAX_SL_DISTANCE_ATR 2.8        // Maximum SL as ATR multiplier"
NEW_CLAMP = """#define MAX_SL_DISTANCE_ATR 6.5        // Maximum SL as ATR multiplier
// WARRANT#489: was 2.8, which clamped the ceiling BELOW the optimum measured in WARRANT#475/#481
// (SL 6.0 ATR won in every confidence band, on 85,641 signals across five instruments). A ceiling
// below the answer does not merely cost performance -- it makes the question untestable from
// inside the build, because calibration can never propose a value the clamp forbids. Raised to 6.5
// so the range CONTAINS the candidate rather than to assert the candidate is right; what the build
// actually uses is still whatever its own calibration measures."""

ANCHOR = "//| NEW: Calculate Smart TP/SL for Trade Execution                   |"

GLOBAL_DECL = (
    "int g_LastBandIndex = -1;   // WARRANT#489: confidence band of the most recent bracket\n"
    "                           // decision, or -1 when no band applied. Read by logging only.\n"
)

BAND_CODE = r"""//| WARRANT#489: CONFIDENCE-BAND BRACKETS                            |
//| The optimal TP:SL ratio moves with confidence -- measured twice, in WARRANT#475 (240 bracket x
//| band cells) and again in WARRANT#481 (all bands run together as one book). Ratio by band:
//|   top 0-2%   1.00      top 2-5%   0.67      top 5-10%  0.67
//|   top 10-15% 0.83      top 15-20% 0.83      below      unchanged
//| Bands are RUNNING QUANTILES of the build's own score margin, not fixed thresholds, so "top 2%"
//| keeps its meaning across rescalings of the score space -- which has already moved twice this
//| campaign. A fixed threshold would quietly come to mean something else after the next
//| recalibration; a quantile cannot.
#define BAND_RING_N        512     // margins retained for the quantile estimate
#define BAND_MIN_SAMPLE     60     // below this there is NO band, not a confident one
double  g_BandRing[BAND_RING_N];
int     g_BandRingCount = 0;
int     g_BandRingHead  = 0;

void RecordScoreMargin(double m) {
    if(!MathIsValidNumber(m) || m < 0.0) return;
    g_BandRing[g_BandRingHead] = m;
    g_BandRingHead = (g_BandRingHead + 1) % BAND_RING_N;
    if(g_BandRingCount < BAND_RING_N) g_BandRingCount++;
}

// Fraction of retained margins strictly below m -- the margin's own percentile.
double ScoreMarginPercentile(double m) {
    if(g_BandRingCount < BAND_MIN_SAMPLE) return -1.0;   // no sample: no answer, not a wrong answer
    int below = 0;
    for(int i = 0; i < g_BandRingCount; i++) if(g_BandRing[i] < m) below++;
    return (double)below / (double)g_BandRingCount;
}

// TP:SL ratio for a margin, by the band it falls in. Returns <=0 when there is no band yet, and
// every caller must leave its existing ratio untouched in that case.
double BandTPRatio(double m, int &bandOut) {
    bandOut = -1;
    double pct = ScoreMarginPercentile(m);
    if(pct < 0.0) return -1.0;              // still learning -- behave exactly as before
    if(pct >= 0.98)      { bandOut = 0; return 1.00; }   // top 0-2%
    else if(pct >= 0.95) { bandOut = 1; return 0.67; }   // top 2-5%
    else if(pct >= 0.90) { bandOut = 2; return 0.67; }   // top 5-10%
    else if(pct >= 0.85) { bandOut = 3; return 0.83; }   // top 10-15%
    else if(pct >= 0.80) { bandOut = 4; return 0.83; }   // top 15-20%
    return -1.0;                            // outside the measured bands: unchanged
}

"""

OLD_TP = (
    "        if(!_r8SLSet) tpslSystem.optimalSLDistance = MathMax(atr * slM * _convMult2, minDist);\n"
    "        tpslSystem.optimalTPDistance = MathMax(atr * tpM * _hrstMult * _waveMult, minDist);"
)
NEW_TP = (
    "        if(!_r8SLSet) tpslSystem.optimalSLDistance = MathMax(atr * slM * _convMult2, minDist);\n"
    "        tpslSystem.optimalTPDistance = MathMax(atr * tpM * _hrstMult * _waveMult, minDist);\n"
    "        // WARRANT#489: re-shape TP to the ratio measured for THIS confidence band. The band\n"
    "        // comes from the running quantile of this build's own score margins, so it means the\n"
    "        // same thing whatever the score space is scaled to. A margin with no band yet -- too\n"
    "        // few samples, or below the 20th percentile -- leaves the distance exactly as the\n"
    "        // existing logic set it, so this can only refine a decision, never invent one.\n"
    "        RecordScoreMargin(_scoreMgn);\n"
    "        int _bandIdx = -1;\n"
    "        double _bandRatio = BandTPRatio(_scoreMgn, _bandIdx);\n"
    "        if(_bandRatio > 0.0 && tpslSystem.optimalSLDistance > 0.0) {\n"
    "            tpslSystem.optimalTPDistance = MathMax(tpslSystem.optimalSLDistance * _bandRatio,\n"
    "                                                   minDist);\n"
    "            g_LastBandIndex = _bandIdx;\n"
    "        } else {\n"
    "            g_LastBandIndex = -1;\n"
    "        }"
)


def main():
    src = io.open(BUILD, encoding="utf-8", errors="surrogateescape", newline="").read()
    before = len(src)
    if "WARRANT#489" in src:
        print("already applied")
        return 0

    for name, old in (("clamp", OLD_CLAMP), ("anchor", ANCHOR), ("tp-site", OLD_TP)):
        if src.count(old) != 1:
            print("REFUSING: %s anchor matched %d times, expected exactly 1."
                  % (name, src.count(old)))
            return 1

    src = src.replace(OLD_CLAMP, NEW_CLAMP, 1)
    src = src.replace(ANCHOR, GLOBAL_DECL + BAND_CODE + ANCHOR, 1)
    src = src.replace(OLD_TP, NEW_TP, 1)

    io.open(BUILD, "w", encoding="utf-8", errors="surrogateescape", newline="").write(src)
    after = len(src)
    print("WARRANT#489 applied to %s" % BUILD.rsplit("\\", 1)[-1])
    print("   chars %d -> %d  (delta %+d)" % (before, after, after - before))
    print("   MAX_SL_DISTANCE_ATR 2.8 -> 6.5   (the clamp that made the finding untestable)")
    print("   + running-quantile confidence bands, TP ratio per band, no-sample -> no change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
