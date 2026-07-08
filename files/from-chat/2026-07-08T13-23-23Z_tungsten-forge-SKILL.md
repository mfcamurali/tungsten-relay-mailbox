# tungsten-forge

**A hybrid hardening + reinforcement agent for TUNGSTEN.**
Version 1.0 — authored from an independent quant audit of 65,000 real EURUSD M5 bars
(2025-03-25 → 2026-02-06) conducted against TUNGSTEN SLS(24)–SLS(28).

This is not a checklist. It is a **thesis, a discrepancy register, and a protocol**, in that
order, because the protocol only makes sense once you understand what was found and — more
importantly — **how the finder was repeatedly wrong.**

---

# PART I — THESIS

## I.1 The Two Programs

Every trading system is two programs: **the one that was designed**, and **the one that runs**.
TUNGSTEN's entire audit history is the story of closing the gap between them. Sixty-plus
defects were found by earlier passes. This agent exists because the last audit found something
worse than defects: it found **logic that had never executed at all**, and **statistics that
could not distinguish evidence from noise**.

## I.2 The Central Discovery

> **Identifying a trend is not the same as predicting profit. TUNGSTEN conflates these everywhere.**

Measured on 65,000 real M5 bars, against a forward R-multiple calibrated so that
`E[R] = 0` under a driftless random walk (see §V.2):

| voice | trend-identification (discrimination) | forward profit (meanR) |
|---|---|---|
| macro EMA200 displacement + slope | **+91.4** (near-perfect) | **−0.003R** (nothing) |
| EMA21 angle | +31.2 | **−0.031R** (loses) |
| DI / ADX | +16.5 | **−0.025R** (loses) |
| Hurst trending | +4.3 (poor) | +0.133R *(p=0.049 — fails correction)* |
| swing DNA (HH/HL) | +2.5 | +0.026R |
| H4 stack | +5.4 | +0.006R |

**At a Bonferroni-corrected bar (12 tests, p < 0.004), not one voice has a real forward edge.**
The best *identifier* of trend earns nothing. Two good identifiers **lose money**.

And the regime-conditional thesis — the load-bearing claim of the entire architecture — fared
no better:

| strategy | meanR | p |
|---|---|---|
| Strong Bull → follow | +0.012 | 0.58 |
| Strong Bear → follow | −0.019 | 0.38 |
| Choppy → fade | −0.026 | 0.38 |
| Breakout (chase new extreme) long | −0.032 | 0.56 |
| Breakout short | −0.117 | 0.065 |

**Nothing.** This does not mean TUNGSTEN cannot work. It means: **edge, if it exists, is not in
simple directional prediction from these features at this horizon and geometry.** Any weight-
learning system pointed at these features will find "edge" — and it will be fiction.

## I.3 The Mechanism By Which Noise Becomes Conviction

A raw Spearman IC computed on a finite sample is **never exactly zero**. Stored raw, a
pure-noise IC of 0.04 becomes a real weight, and the optimizer confidently allocates attention
to nothing. **A self-calibrating system that cannot tell evidence from noise will always find
edge.** This is the single most dangerous failure mode available to TUNGSTEN, because it is
silent, self-reinforcing, and produces beautiful backtests.

The countermeasure (already installed in SLS(26)) is significance shrinkage:

```
SE   = 1/sqrt(n-3)                  # Fisher SE of a rank correlation
ic  *= min(1, |ic| / (2*SE))        # shrink what 2-sigma cannot justify
n<=6 -> ic = 0                      # no information, no weight
```

Verified behaviour: noise ICs (0.02–0.04) collapse to 1–20% of nominal; a genuine IC of 0.30
at n=1000 passes at 100%; a strong IC on thin data (n=40) is discounted to 91%.
**It cannot manufacture edge. It can only refuse to.**

## I.4 The Second Mechanism — Superstition That Survives Shrinkage

Shrinkage defeats *noise*. It does **not** defeat a **large, consistent, high-n, sample-specific**
signal. Measured:

- Trend-following **shorts**: **−0.142R, p < 0.0001, n = 3259**
- Trend-following **longs**: −0.006R, p = 0.76 (flat)

This asymmetry is **not** explained by:
- **Sample drift** — random-walk drift z-score = **0.99** (statistically driftless; the +9.58%
  net move is exactly what a driftless walk produces over 64,700 bars at this ATR).
- **Higher-timeframe conflict** — H4-**aligned** shorts were **worse** (−0.142R) than
  conflicted ones (−0.117R). *The hypothesis was tested and refuted.*

Such a signal sails straight through significance shrinkage untouched. Left alone, TUNGSTEN
would learn **"shorts don't work"** as universal law — from **one instrument, one year**.

The countermeasure rests on what a currency pair **is**: *EURUSD up **is** USD down.* Unlike
equities (borrow cost, upward drift, crash skew), an FX pair has **no structural reason** for
long/short asymmetry. Therefore Strong Bull ↔ Strong Bear, and Bullish Reversal ↔ Bearish
Reversal, are **mirror regimes** whose component ICs should agree unless evidence is
overwhelming. See §III.2 and the SLS(28) implementation.

## I.5 What Was Refuted (and must never be silently reintroduced)

Recording failures is more valuable than recording successes, because failures are what a
future agent will otherwise repeat.

1. **"Zigzag/ATR-significant swing detection beats greedy detection."**
   **REFUTED.** Zigzag discrimination **−7.3** vs greedy **+4.5**. Not shipped.
   Corollary finding: `consecutiveHHHL >= 2` discriminates trend from chop by only **+4.5
   points** (26% vs 21%). The swing-DNA voice is **nearly worthless** for trend identification —
   which is precisely *why* the old Hurst veto's "escape hatch" (`|| consecutiveHHHL>=3`) never
   rescued a real trend.

2. **"M5 Strong Bear is a pullback in an H4 uptrend; H4 alignment will rescue shorts."**
   **REFUTED.** H4-aligned shorts were *worse*. The short-side drag is real and unexplained.

3. **"The SLS(25) trend consensus achieves 89% recognition / 0% false-chop."**
   **REFUTED — by its own author.** The trend label was `|price−EMA200| > 1.5 ATR` and the chop
   label `< 0.5 ATR`, while the rule under test required `≥ 0.8 ATR`. **The rule was graded
   against a definition built from its own input.** Re-validated against an orthogonal label
   (§V.1), the honest figures are:

   | rule | discrimination |
   |---|---|
   | old Hurst veto | **−2.6** (fires *more in chop than in trend* — worse than a coin flip) |
   | consensus, hardcoded 0.8/0.3 | +11.9 |
   | consensus, percentile-learned | **+32.4** |

## I.6 Why Hurst Failed

TUNGSTEN's `ART` header already suspected it: *"on a liquid major at M5, Hurst clusters near
0.50."* The audit proved something stronger.

- Two **correct** Hurst estimators (variance-of-lagged-differences, classic R/S) disagreed on
  the *same* data: one said 82% mean-reverting, the other 80% trending.
- **Synthetic controls settled it:** R/S could not separate a pure trend from mean-reversion at
  this resolution — **0.616 vs 0.621**.
- On 64% of bars in unambiguous structural trend, M5-Hurst read "mean-reverting" **79.3%** of
  the time — suppressing trend classification on **~33,000 genuinely trending bars**.

**Hurst is noise-dominated at M5, and it was wired as the master character gate.** ART fixed the
*boundary*; it could not fix the *primitive*. Hurst is now demoted to one confirming voice.

## I.7 The Replacement Perception (the MA-fan discipline)

Read the 1987 S&P MA-fan study correctly and it teaches an ordering, not an indicator:

> **A trend exists only when the anchor MA is both DISPLACED from price AND SLOPING. Faster
> signals merely confirm it. Displacement alone (flat but far) is range. Slope alone (crossing
> but undisplaced) is noise.**

Encoded as: macro displacement **AND** macro slope are **necessary**; ≥1 faster voice
(H4 stack / DI-ADX / swing DNA / EMA21 angle / Hurst) **confirms**. Percentile-learned
thresholds (disp@p60, slope@p30). Portability verified: **M5 +33.0, M15 +38.9, H1 +25.3**.

## I.8 Dead Logic

Entire branches of TUNGSTEN **have never executed on a forex M5 chart**:

| constant | percentile on EURUSD M5 | consequence |
|---|---|---|
| `priceChange20 > 0.01` | **99.9th** | `+20` score bonus: ~never |
| `priceChange20 > 0.017` | **100th** | `IMPULSE_BREAK` sub-pattern: **unreachable** |
| `priceChange50 > 0.02` | **100th** | classifier branch + `+15` bonus: **unreachable** |
| regime 8 gate (composite) | — | fired **38 times in 65,000 bars (0.06%)** |

Regime 8 is the "Controlled Pullback" the code itself calls the one *"top traders specifically
wait for."* **It is effectively dead in live trading.**

And the root cause runs deeper: **`g_ART.moveSig` — the very field built to abolish hardcoded
thresholds — was clamped to `[0.003, 0.02]`.** That floor sits at the **96.6th percentile on M5**
and the **30.9th on H4**. **ART's own clamps were the pathology ART exists to cure.**

---

# PART II — THE DISCREPANCY REGISTER

Where problems hide. Every future pass audits **all six classes**, on **every subsystem**.

## Class A — SCALE discrepancies
*A number that means one thing on EURUSD M5 and another on USDJPY H4.*

- Absolute price fractions (`> 0.002`, `> 0.01`, `> 0.02`).
- Absolute pip/point constants (`Point * N`). **8 occurrences remain in the file.**
- Any threshold on `priceChange*` (a **fractional return**, not ATR-normalised).
- JPY pairs carry a 100× different quote scale; metals/indices differ again.
- **Measured spread of the problem:** `p55 |priceChange20|` = **0.00065 (M5) → 0.00527 (H4)** —
  an **8× spread across timeframes of a single pair**, before considering other instruments.

## Class B — DISTRIBUTION discrepancies
*ATR-normalisation fixes scale but not shape.*

- A threshold correct at p60 on one instrument may sit at p14 or p99 on another. **`0.8 ATR`
  displacement sat at the 14th percentile of EURUSD M5** — nearly everything cleared it.
- Clamps (`MathMax(a, MathMin(b, x))`) are themselves absolute constants. **Audit every clamp.**
  A clamp that binds is a hardcoded constant in disguise.
- Percentile targets must be chosen against an **orthogonal label**, never by intuition.

## Class C — SYMMETRY discrepancies
*Learning a sample's directional accident as universal law.*

- Long/short asymmetry in a **symmetric instrument** (FX pair) is prima facie suspect.
- In a **drifted instrument** (equity index, crypto) asymmetry may be structural and real.
- **The agent must classify the instrument before applying mirror pooling.** See §III.2.

## Class D — VALIDATION discrepancies
*Grading your own homework. The most dangerous class, because it flatters.*

- **Circularity:** validating a rule against a label built from the rule's own inputs. *(Committed
  by this very audit. Caught. Corrected. −77 percentage points of illusory performance.)*
- **Multiple testing:** ~20 tests were run; at α=0.05 one "significant" result is *expected by
  chance*. The apparent Strong-Bear × Hurst interaction (+0.268R, p=0.0085, n=142) **does not
  survive Bonferroni (p<0.0025) and is almost certainly data-mined noise.**
- **Path ambiguity:** when TP and SL fall inside the same bar, the resolution order biases the
  result. Must be applied **symmetrically** to long and short.
- **In-sample thresholds:** any percentile learned on the same window used for validation.

## Class E — REACHABILITY discrepancies
*Logic that cannot fire, or that always fires.*

- **Dead branches** (fire-rate ≈ 0%): the constant is above the distribution.
- **Saturated branches** (fire-rate ≈ 100%): the constant is below the distribution; the gate
  is decorative and its `if` is a lie.
- Both are invisible in code review and invisible in compilation. **Only a fire-rate audit
  finds them.**

## Class F — NON-STATIONARITY discrepancies
*The window is not the world.*

- Every phase learns one historical window. The suite can prove edge **existed**; nothing can
  certify it **persists**.
- Thin joint cells (regime × score × ATR × hour × tier × HTF) never deepen. Shrinkage makes the
  system **honest** about this; honesty is not abundance.
- Newly-awakened subsystems (loss-side learning, restored phases) have **zero** operational
  history. Unvalidated by definition.

---

# PART III — THE UNIVERSALITY MANDATE

> **The EA must know what it is looking for, and how to find it, on any pair and any timeframe,
> having been told nothing about that pair.**

## III.1 The Three Legal Forms of a Threshold

Every numeric gate in TUNGSTEN must reduce to exactly one of these. **There is no fourth form.**

1. **A percentile of the instrument's own distribution.**
   `thr = ART_Pctile(sortedSamples, n, p)` — with clamps wide enough never to bind on a real
   instrument (degenerate-distribution guard only).
   *Example:* `emaDispTrend = p60(|price−EMA200| / ATR)`.

2. **A ratio to a locally-measured scale.** ATR, realised σ, or another ART field.
   *Example:* `_mvStrong = g_ART.moveSig × 2.3` (≈ p85 by construction).

3. **A dimensionless quantity, provably scale-free.**
   *Example:* `ema21Angle = atan(ΔEMA21 / ATR)` — already ATR-normalised, hence degrees are
   legal. *(Its `12°` cut-point is still Form-1 material and should be ART-learned. **OPEN.**)*

**Horizon scaling law.** Thresholds on an `N`-bar quantity relate to those on an `M`-bar
quantity by the random-walk law `sqrt(N/M)`. Predicted `sqrt(50/20) = 1.58`;
**measured on real data: 1.63.** Confirmed — use it, do not re-derive it per timeframe.

## III.2 Instrument Taxonomy & the Symmetry Prior

Before any mirror pooling, classify the instrument. Two independent signals:

**(a) Structural prior (from the symbol):**
- **SYMMETRIC** — FX majors/minors/crosses (`EURUSD`, `USDJPY`, `GBPAUD`…). Long and short are
  the same trade viewed from either currency. **Full mirror pooling.**
- **QUASI-SYMMETRIC** — metals (`XAUUSD`, `XAGUSD`). Mild structural drift. **Attenuated pooling.**
- **DRIFTED** — equity indices, crypto. Genuine upward drift and crash skew make long/short
  asymmetry *real*. **Mirror pooling must be weak or disabled.**

**(b) Measured prior (from the data):** the random-walk drift z-score over the calibration window:

```
driftZ = |close[last] - close[first]| / (mean(ATR) * sqrt(nBars))
```

Under a driftless walk `driftZ ~ |N(0,1)|`. **Measured on EURUSD M5: driftZ = 0.99 — driftless.**
`driftZ > 2` indicates statistically significant drift.

**Rule:** mirror-pooling strength `λ = 1.0` when both priors say symmetric; attenuate toward
`0` as either prior indicates drift. **Never pool a drifted instrument's mirror regimes.**

> Note: the drift statistic must use the instrument's *contemporaneous* ATR. A constant-ATR
> approximation produces nonsense on exponentially-growing series — verified failure mode.

## III.3 Sensitivity Calibration

"Sensitivity" is where the instrument's *microstructure* meets the strategy's *geometry*:

- **Cost/ATR ratio** — median spread ÷ median ATR. This is the true friction. On an exotic it
  can exceed the edge entirely. Feed it into the growth-rate core (ERM already measures it).
- **Tick value / point scale** — the only place absolute broker constants are legal, and only
  inside `MarketInfo()`-derived conversions.
- **ATR percentile bands** — condition behaviour on volatility *rank*, never on absolute ATR.
- **Session structure varies by pair.** JPY crosses are active in Asia; the 4-session map
  (London/NY/Asia/Sydney) must be **weighted by realised activity**, not assumed.
- **Minimum viable ATR** — if `spread > 0.5 × ATR`, no geometry survives. Refuse to trade.

---

# PART IV — THE PROTOCOL

A **hybrid** pass. Hardening is *defensive* (nothing may fail silently). Reinforcement is
*offensive* (the intelligence must get sharper). They **interleave**, because hardening a
subsystem you are about to redesign wastes the work, and reinforcing a subsystem that silently
fails invents beautiful nonsense.

**Interleaving rule, per subsystem:** `Reinforce → Harden → Validate → Compile`. Never batch.
Never proceed to the next subsystem with a red gate.

## Pass H — HARDENING GATES (defensive)

- **H1 — Reachability audit.** Instrument every gate with a fire-rate counter during
  calibration. Any branch firing `<0.5%` or `>95%` of eligible bars is **flagged as dead or
  saturated**. Report with the constant and its measured percentile. *No exceptions: the
  `IMPULSE_BREAK` sub-pattern and two score bonuses were found this way.*
- **H2 — Clamp audit.** Every `MathMax(a, MathMin(b, x))`: report the fraction of samples where
  the clamp **binds**. A clamp binding >5% of the time is a hardcoded constant in disguise.
- **H3 — Bounds & guards.** Every array access bounds-checked; every `iMA/iATR/iADX/iClose`
  return checked before use; no division without a positive-denominator guard.
- **H4 — Silent-failure ban.** Every conditional adjacent to a logging guard **must** use
  explicit braces. *(A dangling `if(!g_CalibSilent)` amputated three calibration phases. It does
  not get a fourth victim.)*
- **H5 — Scope safety.** Every new variable used only within its declaring function. Verify by
  scanning for a function boundary (`^}`) between declaration and use.
  *(This check caught a real compile break: `_mvImpulse` declared at 3024, used at 3262, with a
  function boundary at 3242.)*
- **H6 — Structural parity.** Brace delta must be `0`; paren delta must **equal the baseline's**
  (string literals legitimately unbalance parens). Compare against the parent build, not zero.
- **H7 — Persistence integrity.** Any new state → guarded-marker tail
  (`0xC59A`, `0xD520`, `0xE210`, next: `0xF115`), `FileIsEnding()`-guarded reads, older files
  degrade safely. Save/load field order traced pair-by-pair.
- **H8 — Determinism.** No calibration result may depend on tick timing, wall-clock, or
  iteration order over a hash. Same bars in → same weights out.

## Pass R — REINFORCEMENT GATES (offensive)

- **R1 — Threshold legality.** Every gate reduced to one of the **three legal forms** (§III.1).
  Any survivor is a defect with a name and a line number.
- **R2 — Significance shrinkage.** Everywhere a correlation becomes a weight:
  `ic *= min(1, |ic|/(2·SE))`, `SE = 1/sqrt(n−3)`, `n≤6 → 0`. **No unguarded channel** —
  the currency-strength IC feeds the same weight path and gets the same treatment.
- **R3 — Mirror pooling.** For mirror pairs `(0,1)` and `(2,3)`, weighted by the symmetry prior
  (§III.2). If `|IC_a − IC_b| ≤ 2σ` of the difference → **pool** (doubles the evidence). Else
  shrink each toward the evidence-weighted pooled estimate by `noise2σ / divergence`.
- **R4 — Measure what you trade.** IC must be correlated against the **signed R-multiple of the
  regime's own simulated geometry**, not against raw forward returns. A component can rank
  returns well and rank *path outcomes* poorly — and path outcomes are what pay.
- **R5 — Prior preservation.** A regime skipped for thin data **retains its prior IC in full**.
  Never blend a prior against an initialisation fallback: that is geometric decay of real
  knowledge into a constant.
- **R6 — Evidence pooling over winner-take-all.** Probability-database queries pool **all**
  matching patterns weighted by `sampleCount × proximity`, then shrink the pooled win-rate
  toward baseline (Beta-Binomial, `k≈12`). One 8-sample bucket must never outvote three
  agreeing 7-sample buckets.
- **R7 — Resurrect, don't delete.** A dead branch (H1) is repaired to its intended **percentile
  rarity**, not removed. `IMPULSE_BREAK` should fire ~p93 of the time it is otherwise eligible;
  it was firing never. *Verify post-fix fire-rates across M5/M15/H1/H4 — they must be comparable.*
- **R8 — Conviction hygiene.** No score bonus, threshold relaxation, or size increase may derive
  from a voice whose measured forward edge is **not distinguishable from zero**. Identifying a
  trend is not predicting profit (§I.2).

---

# PART V — VALIDATION DISCIPLINE

**The rules that stop the agent from fooling itself. Non-negotiable.**

## V.1 The Orthogonal Label Law

> **A rule may never be validated against a label constructed from the rule's own inputs.**

If the rule tests EMA200 displacement, the label may not be an EMA200 displacement threshold.
Approved orthogonal trend label (uses **raw price only**):

```
over a 100-bar window:  R² of a linear regression of close on time
                        slope, ATR-normalised, expressed as total move over the window
TREND := R² > 0.70  AND  |slope·W| > 2.0 ATR
CHOP  := R² < 0.20  AND  |slope·W| < 1.0 ATR
```

This label is independent of EMA200, Hurst, ADX, and swing DNA. It is what exposed the
circularity in §I.5(3) and the −2.6 discrimination of the Hurst veto.

## V.2 The Random-Walk Null

Edge must be measured against a null where **a coin flip earns exactly zero**. For a bracket of
`TP = a·ATR`, `SL = b·ATR`, with `R` measured in units of the SL distance:

```
P(TP first) = b / (a+b)                      # driftless walk
E[R]        = (b/(a+b))·(a/b) + (a/(a+b))·(−1) = 0
```

Verified for `(2.0,1.2) (1.5,1.0) (3.0,1.0) (1.0,1.0)` → all `E[R] = 0.0000`.
**Any TP/SL geometry is a valid null in these units. This is the only admissible edge test.**
Intrabar TP/SL ambiguity must resolve **identically** for long and short.

## V.3 Multiple Testing

Declare the number of hypotheses **before** testing. Report the Bonferroni bar `α/k` alongside
every p-value. **A result that fails correction is noise, however seductive.**
*(Worked example: Strong-Bear × Hurst, +0.268R, p=0.0085, n=142 — fails `p<0.0025`. Discarded.)*

## V.4 Refutation Is a Deliverable

**Ship the refutations.** Two hypotheses died in this audit (zigzag swings; HTF-conflict
explaining short drag) and one published result was retracted by its own author (§I.5(3)).
An agent that reports only its successes is an agent that has stopped testing.

**If a change cannot be shown to improve an orthogonal metric, it does not ship.**

## V.5 The Compile Gate

Zero errors after **every** subsystem, before the next begins. Warnings triaged, not ignored.
Minimal fixes only; report every changed line exactly.

---

# PART VI — EXECUTION SEQUENCE

Base: the newest verified build. Target identity: `SLS(n+1)`. **Never batch subsystems.**

**Stage 0 — Instrument profiling.** Compute and log, from the attached symbol's own history:
`driftZ`; symmetry class; `p55/p60/p85/p93` of `|priceChange20|`, `|priceChange50|`,
`|EMA200 displacement|/ATR`, `|20-bar Δdisplacement|`; median `spread/ATR`. **Nothing else runs
until this profile exists.** Persist it (`0xF115`).

**Stage 1 — Reachability & clamp audit (H1, H2).** Fire-rate every gate; bind-rate every clamp.
Deliver a table: *gate → constant → measured percentile → fire-rate → verdict*.
**Relay checkpoint.**

**Stage 2 — Threshold legality sweep (R1).** Convert every survivor to a legal form (§III.1).
Known remaining offenders: `Point * N` (8 sites); `ema21Angle > 12.0` (Form-3 quantity, Form-1
cut-point). Compile. **Relay checkpoint.**

**Stage 3 — Resurrection (R7).** Repair dead/saturated branches to their intended percentile
rarity. Re-run H1 across **M5/M15/H1/H4** and prove fire-rates are comparable. Compile.

**Stage 4 — Learning integrity (R2, R3, R4, R5, R6).** Shrinkage everywhere; mirror pooling
weighted by the Stage-0 symmetry prior; IC target = signed R-multiple of the regime's own
geometry; prior preservation; evidence pooling. Compile. **Relay checkpoint.**

**Stage 5 — Hardening sweep (H3–H8).** Bounds, guards, braces, scope, parity, persistence,
determinism. Compile.

**Stage 6 — Orthogonal validation (V.1–V.4).** For every behavioural change, report the
orthogonal-label discrimination **before and after**, plus the forward-R with its Bonferroni
bar. **Any change that cannot demonstrate improvement is reverted, and the reversion is
reported.**

**Stage 7 — Ghost gate.** Invalidate stale state, full fresh calibration, Phase 6 ghost to
verdict. Report: calibration duration; IC deltas; ghost WR / PF / trades / verdict; derived
growth rate with the ERM cost haircut; SEG feed status; ERM warm-up state; every anomaly.

**Stage 8 — Hold.** Demo only. **Live attach requires Manuel's explicit go-ahead, after he has
read real numbers.** If the ghost gate refuses, that is the architecture working. Diagnose,
report, hold. **No autonomous re-arm loops.**

---

# PART VII — STANDING PROHIBITIONS

1. **Never** validate a rule against a label derived from its own inputs.
2. **Never** ship a change that has not beaten an orthogonal metric.
3. **Never** let a voice with no measured forward edge add conviction, size, or threshold relief.
4. **Never** introduce an absolute price fraction, pip constant, or unclamped magic number.
5. **Never** pool mirror regimes on a drifted instrument.
6. **Never** delete a dead branch that can be resurrected to its intended rarity.
7. **Never** report a p-value without its multiple-testing bar.
8. **Never** attach to a live funded account without explicit human authorisation.
9. **Never** suppress a refutation. **Ship it.**

---

## Closing

TUNGSTEN's edge — if it exists — is **not** in any single voice, nor in following the regime it
so precisely identifies. Every simple directional hypothesis tested against a correctly
calibrated null came back empty. What the architecture *is* good for is **conditional structure**:
regime × geometry × evidence-weighted precedent, sized so that being wrong is survivable, and
gated by a ghost that can refuse.

This agent's purpose is not to make TUNGSTEN find edge. **It is to make TUNGSTEN incapable of
inventing edge that is not there** — and thereby to make the day it *does* find some
believable.

*The metal is forged. The temper is untested. Only the ghost gate may say otherwise.*
