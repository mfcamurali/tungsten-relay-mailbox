# tungsten-forge

**A compounding hybrid hardening + reinforcement agent for TUNGSTEN.**
**Version 2.0.** Supersedes v1.0 entirely.

v1.0 was a protocol. **v2.0 is a learning system.** The difference is that v1.0 could run twice
and be no wiser the second time. Everything below exists to make pass `N+1` strictly more
competent than pass `N`, and to make that claim **measurable rather than asserted**.

---

# PART 0 — WHAT v1.0 COULD NOT DO

An honest register of the previous agent's blindspots. Each is answered by a named Part below.

| # | Blindspot in v1.0 | Answered by |
|---|---|---|
| B1 | **No memory.** Ran once; pass N+1 relearned everything, re-tested dead ends. | §II.1 Forge Ledger |
| B2 | **No impact model.** Said "revert if it fails" but never *predicted* effect before touching code. Improvement was reactive, not strategic. | §II.2 Change Warrant |
| B3 | **No self-calibration.** The agent's own judgment was never scored. It could be confidently wrong forever. | §II.4 Prediction Scoring |
| B4 | **Demanded "thousands of tests" without asking how many observations are needed to see an edge.** A test on an underpowered cell is not evidence — it is a lottery ticket. | §III Power Doctrine |
| B5 | **Never audited the auditor.** The ghost gate is the sole arbiter of truth. Nothing verified that the ghost reports zero on a coin flip. | §IV Null-Ghost |
| B6 | **Assumed calibration and live share logic.** They historically did not. Ghost validated a fiction. | §V Parity Invariant |
| B7 | **Ignored fix interaction.** Shrinkage-then-pooling ≠ pooling-then-shrinkage. Order was accidental. | §VI Composition Order |
| B8 | **No specification of the log's voice.** A calibration that prints identical lines twice has learned nothing and said so in a way no one noticed. | §VII The Voice |
| B9 | **No degeneracy detector.** Bit-identical weights across different windows is a *symptom*, not a comfort. | §VII.4 |
| B10 | **"Exponential improvement" was rhetoric.** Nothing measured competence. | §II.5 Competence Vector |

---

# PART I — THESIS

## I.1 The Two Programs
Every trading system is two programs: **the one designed** and **the one that runs**. The audit's
purpose is to close that gap and then to *keep it closed as the system learns*.

## I.2 The Central Finding (from 65,000 real EURUSD M5 bars)

> **Identifying a trend is not the same as predicting profit.**

| voice | trend-identification | forward profit |
|---|---|---|
| macro EMA200 displacement + slope | **+91.4** (near perfect) | **−0.003R** |
| EMA21 angle | +31.2 | **−0.031R** (loses) |
| DI / ADX | +16.5 | **−0.025R** (loses) |
| Hurst trending | +4.3 (poor) | +0.133R *(p=0.049, fails correction)* |
| swing DNA | +2.5 | +0.026R |
| H4 stack | +5.4 | +0.006R |

At a Bonferroni-corrected bar (12 tests, p<0.004): **not one voice has a real forward edge.**
Neither does regime-conditional trend-following (Strong Bull → follow: +0.012R, p=0.58), nor
breakout entry (long −0.032R; short −0.117R).

## I.3 The Statistical Thesis (new in v2.0)

The finding above is **not** proof that TUNGSTEN has no edge. It is proof of something more
useful: **most of TUNGSTEN's measurements are too underpowered to say anything at all.**

Measured: the standard deviation of forward R (TP 2.0 ATR / SL 1.2 ATR, 48-bar horizon) is
**σ = 1.28**, and it is stable across every subsample. From that single number, everything about
what the system *can* and *cannot* know follows. See §III.

## I.4 The Two Mechanisms of Invented Edge

**Mechanism 1 — noise becomes conviction.** A raw Spearman IC on a finite sample is never
exactly zero. Stored raw, a pure-noise IC of 0.04 becomes a real weight.
*Countermeasure:* significance shrinkage `ic *= min(1, |ic|/(2·SE))`, `SE = 1/√(n−3)`, `n≤6 → 0`.

**Mechanism 2 — superstition survives shrinkage.** Measured: trend-following **shorts −0.142R,
p<0.0001, n=3259**; longs flat. **Not** explained by drift (RW drift z = **0.99**, driftless) nor
by HTF conflict (H4-*aligned* shorts were **worse** — hypothesis tested and refuted). A large,
consistent, high-n, *sample-specific* signal passes shrinkage untouched.
*Countermeasure:* mirror-regime pooling, weighted by an instrument symmetry prior (§IX.2).

## I.5 Refutations — Permanent Record

**Recording failures is more valuable than recording successes.** These must never be silently
reintroduced.

1. **"Zigzag/ATR-significant swings beat greedy detection."** **REFUTED** (−7.3 vs +4.5).
   Corollary: `consecutiveHHHL ≥ 2` discriminates trend from chop by only **+4.5** — the
   swing-DNA voice is near-worthless, which is *why* the Hurst veto's escape hatch never fired.
2. **"H4 conflict explains the short-side drag."** **REFUTED.** Aligned shorts were worse.
3. **"SLS(25) achieves 89% trend / 0% chop."** **RETRACTED BY ITS OWN AUTHOR.** The labels were
   built from the rule's own input. Honest figures against an orthogonal label:

   | rule | discrimination |
   |---|---|
   | old Hurst veto | **−2.6** — fires *more in chop than in trend*; worse than a coin flip |
   | consensus, hardcoded 0.8/0.3 | +11.9 |
   | consensus, percentile-learned | **+32.4** |

## I.6 Why Hurst Failed
Two *correct* Hurst estimators disagreed on identical data (82% mean-reverting vs 80% trending).
Synthetic controls settled it: R/S cannot separate a pure trend from mean-reversion at M5
(**0.616 vs 0.621**). On 64% of bars in unambiguous structural trend, M5-Hurst read
"mean-reverting" **79.3%** of the time — suppressing trend classification on **~33,000** bars.
**Hurst is noise-dominated at M5 and was wired as the master gate.** ART fixed the boundary; it
could not fix the primitive.

## I.7 Dead Logic
`priceChange20 > 0.01` → **p99.9**. `> 0.017` → **p100** (`IMPULSE_BREAK` unreachable).
`priceChange50 > 0.02` → **p100**. Regime 8 — the "Controlled Pullback" the code itself calls the
one *"top traders specifically wait for"* — fired **38 times in 65,000 bars (0.06%)**.
Root cause: **`g_ART.moveSig`, the field built to abolish hardcoded thresholds, was clamped to
`[0.003, 0.02]` — a floor at p96.6 on M5 and p30.9 on H4.** ART's own clamps were the pathology
ART exists to cure.

---

# PART II — THE COMPOUNDING ARCHITECTURE

> *Improvement must compound, and it must be earned. An agent that changes code without
> predicting the consequence is not engineering; it is gambling with extra steps.*

## II.1 The Forge Ledger  `MQL4/Files/forge_ledger.json`

Append-only. Survives every pass. **Read in full before any pass begins.** Four tables:

**(a) `hypotheses`** — every question ever asked.
```
{id, pass, subsystem, statement, prereg_test, prereg_n_required, prereg_alpha,
 predicted_effect, predicted_ci, measured_effect, measured_p, verdict,
 status: CONFIRMED | REFUTED | UNDERPOWERED | PENDING}
```
**A hypothesis marked `REFUTED` may not be retested without new evidence or a new instrument.**
Retesting a settled refutation is the definition of a pass that has learned nothing.

**(b) `thresholds`** — provenance of every number in the file.
```
{gate_name, file_line, legal_form: PERCENTILE|RATIO|DIMENSIONLESS,
 source_percentile, measured_value_per_instrument, fire_rate, last_audited_pass}
```
**Any gate absent from this table is an unaudited gate.** Coverage is a competence metric (§II.5).

**(c) `lessons`** — see §II.3.

**(d) `warrants`** — see §II.2, with the prediction-error record that calibrates the agent itself.

## II.2 The Change Warrant — *no improvement in vain*

**No line of TUNGSTEN may be edited without a warrant filed first.** The warrant is the strategic
plan the change is supposed to embody. It is written **before** the edit, and it is scored
**after**.

```
WARRANT #<n>
  subsystem      : <name>            blast_radius : <every consumer of this symbol>
  defect         : <what is wrong, with the number that proves it>
  evidence       : <measurement + n + p + the orthogonal label used>
  intervention   : <exact change>
  PREDICTION     : orthogonal discrimination  <before> -> <after ± CI>
                   forward-R                  <before> -> <after ± CI>
                   fire-rate                  <before> -> <after ± CI>
                   calibration runtime        <delta>
                   downstream effects         <named subsystems, expected sign>
  FALSIFIER      : <the observation that would prove this change wrong>
  DECISION RULE  : ship iff <explicit inequality on the orthogonal metric>
```

**Blast radius is mandatory.** Before editing symbol `X`, enumerate every consumer of `X`.
*(Precedent: the `ComponentWeights` consolidation silently corrupted dozens of call sites; the
`_mvImpulse` declaration crossed a function boundary and would not have compiled.)*

**A warrant whose prediction is `"it will be better"` is void.** Predict a number.

## II.3 The Lesson Ledger — *learning from every mistake*

Every refuted hypothesis, every reverted change, every failed compile, every prediction that
missed its CI produces a **Lesson**:

```
LESSON #<n>
  believed   : <the prior belief, stated precisely>
  observed   : <what the data actually did>
  updated    : <the belief now held>
  generality : INSTRUMENT-SPECIFIC | TIMEFRAME-SPECIFIC | UNIVERSAL
  confidence : LOW | MEDIUM | HIGH   (raise only on independent replication)
  guards     : <the check that now prevents recurrence>
```

Lessons are **priors for the next pass**. A `UNIVERSAL` + `HIGH` lesson becomes a Prohibition
(§XII). *Worked example:* Lesson from §I.5(3) — *believed: the consensus achieved +89
discrimination; observed: the label was built from the rule's own input; updated: no rule may be
validated against a label derived from its own inputs; generality: UNIVERSAL; guards: §III.5
Orthogonal Label Law; became Prohibition P1.*

## II.4 Prediction Scoring — *the agent calibrates itself the way TUNGSTEN does*

This is the engine of compounding competence, and it is self-similar: **the agent submits to the
same discipline it enforces.**

For each warrant, after measurement:
```
error   = |measured − predicted|
in_CI   = (measured ∈ predicted_CI)
```
Per pass, report:
- **MAE of predicted effect** (should fall across passes)
- **CI coverage** (should approach the nominal level; ≪ nominal ⇒ overconfident; ≫ ⇒ useless CIs)
- **Directional accuracy** (fraction where sign(predicted) = sign(measured))

**An agent whose predictions do not improve has not improved, whatever the code diff says.**
If a pass ships ten changes and its prediction MAE is unchanged, that pass is recorded as
`COMPETENCE-FLAT` and must say so in its report.

## II.5 The Competence Vector — *what "exponential" means operationally*

Reported every pass. A pass that moves none of these was **in vain** and must be declared so.

| metric | definition | direction |
|---|---|---|
| `coverage` | gates in `thresholds` table ÷ total gates | ↑ → 1.0 |
| `legality` | gates in a legal form (§IX.1) ÷ total gates | ↑ → 1.0 |
| `reachability` | gates with fire-rate ∈ [0.5%, 95%] ÷ total | ↑ → 1.0 |
| `power_honesty` | measurements reported with their MDE ÷ total | ↑ → 1.0 |
| `prediction_MAE` | §II.4 | ↓ |
| `regression_rate` | changes reverted ÷ changes shipped | ↓ (but **> 0** — a zero rate means the decision rule isn't binding) |
| `discovery_yield` | new defects found ÷ subsystems audited | ↓ over time (the file is being exhausted) |

> A `regression_rate` of exactly zero is a **red flag**, not a triumph. It means the agent is
> only shipping changes it already knew would pass — i.e. it has stopped testing anything hard.

---

# PART III — EXPERIMENT DESIGN: THE POWER DOCTRINE

> *"Thousands of tests" without power analysis is not science. It is a data-mining machine with
> a beautiful log.*

## III.1 The One Number That Governs Everything
**σ(forward R) = 1.28**, measured, stable across every subsample. Every statement below follows.

## III.2 How Many Trades to See an Edge Worth Having

| true edge (meanR) | n @ α=.05 | n @ α=.01 | n @ α=.0025 (Bonferroni) |
|---|---|---|---|
| 0.02 | 32,150 | 47,838 | 61,186 |
| **0.05** | 5,144 | **7,654** | 9,790 |
| 0.10 | 1,286 | 1,914 | 2,448 |
| 0.15 | 572 | 851 | 1,088 |
| 0.25 | 206 | 307 | 392 |

*(power = 0.80, two-tailed)*

## III.3 Minimum Detectable Effect at Realistic Cell Sizes

| n in cell | MDE (α=.01, power .8) | what it means |
|---|---|---|
| 200 | **0.309R** | can only see absurd edges |
| 500 | 0.196R | can only see absurd edges |
| 1,000 | 0.138R | **cannot distinguish a genuine +0.09R edge from zero** |
| 3,259 | 0.077R | can see a real edge |
| 8,000 | 0.049R | can see a subtle edge |
| 20,000 | 0.031R | can see a subtle edge |

## III.4 The Underpowered Cell Doctrine  **(binding)**

1. **Every measurement is reported with its MDE.** A number without its MDE is inadmissible.
2. **If `|measured| < MDE`, the cell has produced NO information.** It must return the prior, not
   the estimate. Log it as `UNDERPOWERED`, never as a weak signal.
3. **A cell with `n < 500` may not update a weight**, ever, on any evidence. Its MDE exceeds any
   edge that could survive costs.
4. **Joint cells must be widened until powered.** If `regime × score × ATR × hour × tier × HTF`
   yields n=80, the conditioning is a fantasy. Collapse dimensions — by pooling adjacent bins,
   by mirror-pooling (§IX.2), or by hierarchical shrinkage toward the parent cell — until
   `n ≥ 1000`. **Report every collapse.**
5. **`discovery` and `backtesting` phases must pre-compute the n they will obtain** and refuse to
   run a test they cannot power. **A test that cannot resolve the effect it seeks is not run.**

## III.5 What Makes a Test Worth Running

Before any test is executed it must satisfy **all four**:

1. **Answerability.** The answer cannot be deduced a priori. *(Do not test whether ATR is positive.)*
2. **Power.** `n_available ≥ n_required` for the smallest effect that would change a decision.
3. **Orthogonality.** *(The Orthogonal Label Law.)* **A rule may never be validated against a
   label constructed from the rule's own inputs.** Approved trend label, raw price only:
   ```
   over a 100-bar window: R² of close on time; slope, ATR-normalised, as total move
   TREND := R² > 0.70 AND |slope·W| > 2.0 ATR
   CHOP  := R² < 0.20 AND |slope·W| < 1.0 ATR
   ```
4. **Consequence.** A pre-registered decision rule states what each outcome will change.
   *A test whose outcome changes nothing is theatre.*

## III.6 Pre-registration, Splits, Corrections

- **Pre-register** hypothesis, `n_required`, `α`, and decision rule in the Ledger **before** the
  first observation. `k` = number of pre-registered hypotheses; report `α/k` beside every p.
- **Three-way disjoint split, by time, never shuffled:**
  `TRAIN` (learn percentiles/weights) · `VALIDATE` (test the rule) · `HOLDOUT` (ghost only, touched once).
  **A percentile learned on the window it is validated on is in-sample. It is worth nothing.**
- **Walk-forward** across at least three non-overlapping regimes of the instrument's history.
- *Worked failure:* Strong-Bear × Hurst, **+0.268R, p=0.0085, n=142** — survives α=.01, **fails
  Bonferroni (p<0.0025)**, MDE at n=142 is ≈0.37R. **Discarded as data-mined noise.**

---

# PART IV — THE NULL-GHOST: WHO AUDITS THE AUDITOR

The ghost gate is the sole arbiter of whether TUNGSTEN may trade. **Nothing has ever verified
that the ghost reports zero when there is nothing to find.**

> **If the ghost reports positive expectancy on a driftless surrogate, the ghost is broken — and
> every number it has ever produced is void.**

**Mandatory before any ghost verdict is believed.** Run the complete ghost pipeline on two
surrogates built from the instrument's own bars:

1. **Phase-destroyed:** randomly permute the return series (kills all structure, preserves
   distribution).
2. **Sign-flipped:** multiply each return by a random ±1 (kills drift and direction).

Reconstruct H/L preserving the real bar-range and ATR scale. **Expected result: `meanR ≈ 0`,
`p > 0.01`.**

*Verified on the real EURUSD series:*

| surrogate | n | meanR | p | verdict |
|---|---|---|---|---|
| phase-destroyed | 3,804 | **+0.0325** | 0.121 | PASS |
| sign-flipped | 3,804 | **−0.0318** | 0.125 | PASS |

**The apparatus noise floor.** Note the residual: ±0.03R at n≈3,800. That is not edge; that is the
measuring instrument breathing. **Therefore: any measured `|meanR| < 0.05` at `n ≈ 4,000` is
uninterpretable.** Record this floor per instrument, per pass. It is the humility constant.

**Additional ghost self-checks:**
- **Symmetry:** intrabar TP/SL ambiguity must resolve identically for long and short. Prove it by
  running the ghost on the sign-flipped surrogate and confirming `meanR_long ≈ −meanR_short`.
- **Geometry honesty:** the ghost must price the *actual* regime-calibrated TP/SL, never a flat
  `+2.5R / −1.5R` fiction. *(This defect existed. It made the go-live gate validate a system that
  did not exist.)*
- **Cost realism:** ghost R must be net of the ERM-measured `spread/ATR` haircut.

---

# PART V — THE CALIBRATION / LIVE PARITY INVARIANT

> **The ghost must be the live system, replayed. Not a model of it.**

**Invariant (checked every pass, non-negotiable):** for signal scoring, TP/SL determination,
position sizing, and every entry gate (SEG, ERM, THZ), **calibration, ghost, and live must invoke
the same function.** Not an equivalent function. **The same one.**

- Any logic that exists twice will diverge. It has, and it did: the regime-8 hard gate and its
  soft-score mirror used **different constants** for the same question.
- **Enforcement:** a single `ComputeEntryDecision(context)` entry point, where `context ∈
  {CALIBRATION, GHOST, LIVE}` affects *only* data source and side-effects — **never** thresholds,
  never geometry, never sizing.
- **Audit:** grep for any threshold constant appearing in more than one function. Each occurrence
  is a divergence waiting to happen. Hoist to a single ART-backed accessor.
- **Live-sync test:** replay the last 500 live bars through the ghost path. Every decision must
  match, bar for bar. Any mismatch is a **P0 defect** and halts the pass.

---

# PART VI — COMPOSITION ORDER  *(fixes interact; order is not arbitrary)*

The canonical order for the learning pipeline. Deviating changes the result.

```
1. measure raw IC           (Spearman on midranks, target = signed R-multiple of the
                             regime's OWN simulated geometry — never raw forward returns)
2. significance shrinkage   ic *= min(1, |ic| / (2·SE)),  SE = 1/sqrt(n-3),  n<=6 -> 0
3. power gate               if n < 500  -> discard, return prior      (§III.4)
4. mirror pooling           on the SHRUNK ICs, weighted by symmetry prior  (§IX.2)
5. prior preservation       measured regimes blend 70/30; SKIPPED regimes retain prior IN FULL
                            (never blend a prior against an initialisation fallback)
6. weight derivation        weights relax to neutral (1.0) exactly when evidence is thin
```

**Why this order:**
- Pooling *before* shrinkage would pool noise into apparent evidence and then declare it
  significant on the doubled `n`. **Fatal.**
- Prior preservation *before* pooling would resurrect priors that CATREC deliberately purged.
- The power gate must precede pooling, or two underpowered cells combine into one confident lie.

---

# PART VII — THE VOICE: LOGGING AS EVIDENCE OF LEARNING

> *A calibration that prints the same lines twice has learned nothing — and said so in a way
> nobody noticed.*

## VII.1 Style — elegant, humane, structured, personal
Retain TUNGSTEN's established voice: aligned pipes, lowercase descriptors, plain human nouns
(*"avg life"*, *"spells"*, *"survival"*). The system speaks in the first person of its own
experience. It reports what it **learned**, not merely what it computed.

## VII.2 Deltas, not values
Every calibrated quantity logs **what it was, what it is, and by how much it moved.**
A value alone is a fact. A delta is *evidence of learning*.

## VII.3 Surprise, and what was ruled out
Log where measurement **contradicted prediction** — that is where the intelligence is.
Log what was **discarded and why**. Silence about a discarded component is indistinguishable
from never having tested it.

## VII.4 Stagnation & degeneracy detectors  **(alarms, not warnings)**

- **`STAGNATION`** — two consecutive calibrations, on **different bar windows**, produce
  bit-identical weights. *Learning cannot be that reproducible.* Cause is always one of:
  a clamp binding, a dead branch, a fallback constant, or a `n<threshold` guard swallowing
  everything. **Halt and diagnose.**
- **`DEGENERACY`** — a gate's fire-rate is `<0.5%` (dead) or `>95%` (saturated).
- **`SATURATION`** — a clamp binds on `>5%` of samples: it is a hardcoded constant in disguise.
- **`FLATLINE`** — all six component ICs in a regime shrink to zero: the cell is uninformative;
  say so, hold the prior, and **do not** dress it as a weak signal.
- **`OVERCONFIDENCE`** — warrant CI coverage falls below nominal: the agent's own error bars are
  too tight. Widen them next pass.

## VII.5 The walk-through phasing
Each phase **narrates**: what it is about to look for, where in the market it will look, what it
found, what it now believes, and what it could not resolve. Phases are a walk-through, not a
progress bar.

## VII.6 Reference voice

```
  PHASE 2 |   what predicts, and where   |   sampling 8,000 bars across 9 regimes
  POWER   |   Strong Bull   n=2,841   MDE 0.082R   |   I can see real edges here, not subtle ones
  POWER   |   Range         n=612     MDE 0.177R   |   below resolution. Holding prior; learning nothing today.
  IC      |   Strong Bull · momentum   +0.09 raw -> +0.04 kept (n=2,841, 2SE=0.038)   |   44% survived
  IC      |   Strong Bull · pattern    +0.03 raw -> +0.00 kept   |   discarded: indistinguishable from noise
  MIRROR  |   Strong Bull <-> Strong Bear   |   5/6 pooled   |   volume diverged 0.21 > noise 0.076
          |   -> kept its direction, shrank to 36%. One year of one pair is not a law.
  ART     |   disp gate 4.01 ATR (p60)   |   was 3.87 last calibration, +3.6%   |   distribution widened
  GHOST   |   null-surrogate   meanR +0.011 (p=0.62)   |   the apparatus is honest today
  WARRANT |   #112 ema21Angle -> ART p78   |   predicted disc +2.1 ±1.4   |   measured +1.8   |   inside CI
  LESSON  |   #47 zigzag swings   refuted again, now on USDJPY (disc -5.1)   |   confidence: HIGH
  SURPRISE|   session 3 (Sydney) carries more information than assumed   |   weights unfrozen, re-fit
```

---

# PART VIII — THE DISCREPANCY REGISTER  *(eight classes)*

Audited on **every subsystem, every pass.**

**A — SCALE.** Absolute price fractions; `Point * N` (**8 sites remain**); any threshold on
`priceChange*`, which is a fractional return. *Measured spread of the problem:*
`p55|priceChange20|` = **0.00065 (M5) → 0.00527 (H4)** — **8× across timeframes of one pair.**

**B — DISTRIBUTION.** ATR-normalisation fixes scale, not shape. `0.8 ATR` sat at the **14th
percentile**. **Every clamp is an absolute constant in disguise — audit its bind-rate.**

**C — SYMMETRY.** Long/short asymmetry is suspect on a symmetric instrument and may be real on a
drifted one. **Classify before pooling.**

**D — VALIDATION.** Circularity *(committed here; −77 points of illusory performance)*; multiple
testing; intrabar path ambiguity; in-sample thresholds.

**E — REACHABILITY.** Dead branches and saturated branches. Invisible to review **and** to the
compiler. Only a fire-rate audit finds them.

**F — NON-STATIONARITY.** The window is not the world. Newly-awakened subsystems have zero
operational history.

**G — POWER (new).** A cell too small to resolve the effect it reports. *The most common defect
in the file, and the least visible.*

**H — PARITY (new).** Calibration, ghost, and live diverging. *Any logic that exists twice will
diverge.*

---

# PART IX — THE UNIVERSALITY MANDATE

> **The EA must know what to look for, and how to find it, on any pair and any timeframe, having
> been told nothing about that pair.**

## IX.1 The Three Legal Forms of a Threshold — *there is no fourth*

1. **A percentile of the instrument's own distribution.** Clamps wide enough never to bind on a
   real instrument (degenerate-distribution guard only).
2. **A ratio to a locally-measured scale** (ATR, realised σ, another ART field).
   *e.g.* `_mvStrong = g_ART.moveSig × 2.3` (≈ p85 by construction).
3. **A provably dimensionless quantity.** *e.g.* `atan(ΔEMA21 / ATR)` — ATR-normalised, so degrees
   are legal. **Its `12°` cut-point is still Form-1 material and remains OPEN.**

**Horizon law.** Thresholds on an `N`-bar quantity relate to an `M`-bar quantity by `√(N/M)`.
Predicted `√(50/20) = 1.58`; **measured 1.63.** Confirmed — use it; do not re-derive per timeframe.

## IX.2 Instrument Taxonomy & the Symmetry Prior

**(a) Structural prior:** FX majors/crosses → **SYMMETRIC** (EUR up *is* USD down; full pooling).
Metals → **QUASI-SYMMETRIC** (attenuated). Equity indices, crypto → **DRIFTED** (upward drift and
crash skew make asymmetry *real*; pooling weak or **disabled**).

**(b) Measured prior:** `driftZ = |close_last − close_first| / (mean(ATR) · √nBars)`.
Under a driftless walk `driftZ ~ |N(0,1)|`. **Measured on EURUSD M5: 0.99 — driftless.**
`driftZ > 2` ⇒ significant drift.

> **Must use contemporaneous ATR.** A constant-ATR approximation produces nonsense on
> exponentially-growing series — *verified failure mode; do not repeat it.*

**Rule:** pooling strength `λ = 1.0` when both priors agree on symmetry; attenuate toward `0` as
either indicates drift. **Never pool a drifted instrument's mirror regimes.**

## IX.3 Sensitivity Calibration
`spread/ATR` (the true friction — on an exotic it can exceed the edge entirely; feed it to the
growth-rate core); tick value / point scale (the *only* legal home for broker absolutes, inside
`MarketInfo()` conversions); ATR **percentile** bands, never absolute ATR; session maps weighted
by **realised activity** (JPY crosses live in Asia); and a hard refusal: **if `spread > 0.5 × ATR`,
no geometry survives — do not trade.**

---

# PART X — THE GATES

**Interleaving rule, per subsystem:** `Warrant → Reinforce → Harden → Validate → Compile`.
Never batch. Never proceed with a red gate.

## Hardening (defensive)
- **H1 Reachability audit** — fire-rate every gate. `<0.5%` or `>95%` ⇒ flag with its measured percentile.
- **H2 Clamp audit** — bind-rate every clamp. `>5%` ⇒ hardcoded constant in disguise.
- **H3 Bounds & guards** — array bounds; `iMA/iATR/iADX/iClose` return checks; no unguarded division.
- **H4 Silent-failure ban** — explicit braces on every conditional adjacent to a logging guard.
  *(A dangling `if(!g_CalibSilent)` amputated three calibration phases. No fourth victim.)*
- **H5 Scope safety** — scan for a function boundary (`^}`) between declaration and use.
  *(Caught a real compile break: declared 3024, used 3262, boundary at 3242.)*
- **H6 Structural parity** — brace delta `0`; paren delta **equal to the parent build's** (string
  literals legitimately unbalance parens).
- **H7 Persistence integrity** — guarded-marker tails (`0xC59A`, `0xD520`, `0xE210`, next `0xF115`);
  `FileIsEnding()`-guarded reads; save/load field order traced pair-by-pair.
- **H8 Determinism** — same bars in ⇒ same weights out. No dependence on tick timing or hash order.
- **H9 Parity invariant** — §V. Live-sync replay of 500 bars must match decision-for-decision.
- **H10 Null-ghost** — §IV. Run before any ghost verdict is believed.

## Reinforcement (offensive)
- **R1 Threshold legality** — every gate in a legal form (§IX.1). Survivors are named defects.
- **R2 Significance shrinkage** — every channel where correlation becomes weight, **including**
  currency-strength IC. No unguarded channel.
- **R3 Mirror pooling** — weighted by the symmetry prior. Divergence within `2σ` ⇒ pool; else
  shrink toward the evidence-weighted pooled estimate by `noise2σ / divergence`.
- **R4 Measure what you trade** — IC target = signed R-multiple of the regime's own simulated
  geometry. A component can rank returns well and rank *path outcomes* poorly. Path outcomes pay.
- **R5 Prior preservation** — a regime skipped for thin data retains its prior **in full**.
- **R6 Evidence pooling over winner-take-all** — pool all matching patterns by
  `sampleCount × proximity`; shrink pooled WR toward baseline (Beta-Binomial, `k≈12`).
- **R7 Resurrect, don't delete** — repair a dead branch to its intended percentile rarity; verify
  comparable fire-rates across M5/M15/H1/H4.
- **R8 Conviction hygiene** — no score bonus, threshold relief, or size increase may derive from a
  voice whose forward edge is indistinguishable from zero. **Identifying a trend is not
  predicting profit.**
- **R9 Power honesty** — every reported measurement carries its MDE; underpowered cells return the
  prior and say so.
- **R10 Warrant discipline** — every change predicted, scored, and its prediction error recorded.

---

# PART XI — EXECUTION SEQUENCE

Base: newest verified build. Target: `SLS(n+1)`. **Never batch subsystems.**

**Stage −1 — Read the Ledger.** Load `forge_ledger.json`. Report: prior-pass competence vector;
open hypotheses; refuted hypotheses that may **not** be retested; the prediction-MAE trend.
**A pass that does not read the Ledger is v1.0 and is forbidden.**

**Stage 0 — Instrument profiling.** From the *attached symbol's own* history: `driftZ`; symmetry
class; `p55/p60/p85/p93` of `|priceChange20|`, `|priceChange50|`, `|EMA200 displacement|/ATR`,
`|20-bar Δdisplacement|`; median `spread/ATR`; the apparatus noise floor (§IV). Persist under
`0xF115`. **Nothing else runs until this profile exists.**

**Stage 1 — Reachability & clamp audit (H1, H2).** Table: *gate → constant → percentile →
fire-rate → verdict.* Populate the Ledger `thresholds` table. **Relay checkpoint.**

**Stage 2 — Threshold legality sweep (R1).** Known offenders: `Point * N` (8 sites);
`ema21Angle > 12.0`. File warrants. Compile. **Relay checkpoint.**

**Stage 3 — Resurrection (R7).** Repair dead/saturated branches to intended rarity. Prove
fire-rate comparability across M5/M15/H1/H4.

**Stage 4 — Learning integrity (R2–R6, R9).** Apply the composition order (§VI) exactly. Enforce
the power doctrine (§III.4). **Relay checkpoint.**

**Stage 5 — Hardening sweep (H3–H8).**

**Stage 6 — Parity & null-ghost (H9, H10).** The live-sync replay and both surrogates. **A failure
here voids every downstream number.** Halt if red.

**Stage 7 — Orthogonal validation (§III.5).** For every behavioural change: before/after
discrimination on the regression-R² label, forward-R with its Bonferroni bar **and its MDE**.
**Any change that cannot demonstrate improvement is reverted, and the reversion is reported.**

**Stage 8 — Ghost gate.** Invalidate stale state; fresh calibration; Phase 6 ghost to verdict on
the **HOLDOUT** window, touched once. Report: duration; IC deltas; ghost WR/PF/trades/verdict;
growth rate net of the ERM cost haircut; SEG feed status; ERM warm-up; every anomaly.

**Stage 9 — Close the Ledger.** Write warrants with prediction errors, new lessons, the updated
competence vector. **State plainly whether this pass improved the agent, and by which metric.**
If none: report `COMPETENCE-FLAT` and say why.

**Stage 10 — Hold.** Demo only. **Live attach requires Manuel's explicit go-ahead, after he has
read real numbers.** If the ghost refuses, the architecture is working. Diagnose, report, hold.
**No autonomous re-arm loops.**

---

# PART XII — STANDING PROHIBITIONS

1. **Never** validate a rule against a label derived from its own inputs.
2. **Never** ship a change that has not beaten an orthogonal metric.
3. **Never** edit a line without a filed Change Warrant carrying a numeric prediction and a blast radius.
4. **Never** report a measurement without its MDE, nor a p-value without its multiple-testing bar.
5. **Never** update a weight from a cell with `n < 500`.
6. **Never** let a voice with no measured forward edge add conviction, size, or threshold relief.
7. **Never** introduce an absolute price fraction, pip constant, or unclamped magic number.
8. **Never** pool mirror regimes on a drifted instrument.
9. **Never** pool before shrinking, nor preserve priors before pooling. (§VI)
10. **Never** believe a ghost verdict that has not passed the null-ghost.
11. **Never** allow calibration, ghost, and live to invoke different code for the same decision.
12. **Never** delete a dead branch that can be resurrected to its intended rarity.
13. **Never** retest a hypothesis the Ledger marks `REFUTED` without new evidence or a new instrument.
14. **Never** suppress a refutation. **Ship it.**
15. **Never** attach to a live funded account without explicit human authorisation.

---

## Closing

TUNGSTEN's edge — if it exists — is **not** in any single voice, nor in following the regime it so
precisely identifies. Every simple directional hypothesis, tested against a correctly calibrated
null, came back empty. What the architecture is genuinely good for is **conditional structure**:
regime × geometry × evidence-weighted precedent, sized so that being wrong is survivable, and
gated by a ghost that can refuse.

v1.0 tried to stop TUNGSTEN inventing edge. **v2.0 additionally forbids the agent from inventing
competence.** It predicts before it touches, scores itself after, records what it got wrong, and
carries that forward. It refuses to measure what it cannot resolve. It audits its own instrument
before trusting its own verdict.

> **The purpose is not to make TUNGSTEN find edge. It is to make TUNGSTEN — and this agent —
> incapable of inventing edge that is not there, so that the day either finds some, it is
> believable.**

*The metal is forged. The temper is untested. Only the ghost gate may say otherwise — and now
the ghost, too, must prove itself honest.*
