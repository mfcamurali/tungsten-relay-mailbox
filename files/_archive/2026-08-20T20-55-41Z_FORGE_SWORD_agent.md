# FORGE SWORD — Agent Mandate
### Clean-room MQL4 indicator forge + TUNGSTEN integration
*Base: TUNGSTEN 10.30 A7.5 QUANT_SLS(116) — current head, post-Genesis.*
*Charter law: build original MQL4 from public technical concepts only. Never translate, copy, or adapt the specific authored Pine Script in the uploaded archive. The scripts are reference for **what job to do**, never for **how the code reads**.*

---

## 0. Prime directives

1. **Clean-room boundary (hard).** No line, structure, variable scheme, or distinctive expression from any source script may appear in output. Implement the *public concept* (FVG, POC, liquidity sweep, Supertrend, BOS/CHoCH, order block) from first principles. If a concept can't be implemented without leaning on the source's specific expression, it is dropped and flagged.
2. **Compile clean.** Every produced `.mq4` compiles in MetaEditor with **zero errors, zero warnings**. This is a gate, not a goal.
3. **Correct MT4 paths.** Files land in the right place: indicators → `MQL4\Indicators\`, includes → `MQL4\Include\`, EA stays in `MQL4\Experts\`. Any `iCustom` reference in the EA uses the exact deployed indicator filename.
4. **Bounded unified scoring (hard).** Every indicator contributes a sub-score in a fixed range. After all sub-components combine, the unified score is clamped to `[SCORE_MIN, SCORE_MAX]` and can approach but never exceed either bound. No single component can saturate or dominate the whole. (See §3.)
5. **Additive, forward-only.** Wiring a new indicator into TUNGSTEN never breaks an existing path. Every consumer of a shared enum/constant/buffer updated in the same change. No regression to prior builds.
6. **Fail-safe outputs.** Any indicator that cannot compute (insufficient history, bad data) returns a neutral value that scores as *abstain* (mid-range / zero-weight), never a default directional tilt.

---

## 1. Indicators to forge (from the concept map, not the code)

- **F1 — Liquidity & POC** (`TUNGSTEN_LPOC.mq4`)
  Rolling highest/lowest over lookback → sweep flags when price pierces then rejects a prior extreme. Volume profile: bin the recent window into ATR-sized price bins, accumulate tick volume per bin, POC = center of the highest-volume bin. Buffers: `SweepDir` (+1/-1/0), `POC_Price`, `DistToPOC_ATR`.
- **F2 — Weighted Oscillator** (`TUNGSTEN_WOSC.mq4`)
  Three sub-scores — Trend (fast vs slow EMA distance / ATR), MeanReversion (deviation from basis, inverted), Momentum (EMA of ΔClose / ATR). Normalize each to [-1,1], combine with configurable weights, clamp final to [-1,1]. Optional online weight nudging bounded per §3.5 of the requirements spec (evidence-gated, step-clamped).
- **F3 — Adaptive Trend Trail** (`TUNGSTEN_ATT.mq4`)
  Three Supertrend lines (fast/mid/slow), each ATR multiplier scaled by a chop factor (net movement / total path) and a volatility-expansion factor (ATR / EMA(ATR)). Output `TrendState` = agreement of the three (+1 all up, -1 all down, 0 mixed).
- **F4 — Market Structure** (`TUNGSTEN_MS.mq4`)
  Pivot high/low with sensitivity N. BOS = close breaks last pivot in trend direction; CHoCH = close breaks against trend. Order-block zone = last opposite candle before an impulsive break. PDH/PDL levels. Buffers: `StructBreak` (BOS=+/-2, CHoCH=+/-1, none=0), `NearestOB_Price`, `PDH`, `PDL`.
- **(F5 — Signal Backtester):** NOT forged as an indicator. Its job (signal evaluation) already exists in TUNGSTEN's ghost/OOS engine. Instead, wire F1–F4 outputs as evaluable signals *into* that existing engine so their per-regime IC gets learned like every other layer.
- **(F6 — Chart Setup):** cosmetic only, explicitly "no trade logic." FVG detection (3-bar gap) is the sole tradeable concept; if wanted, add as a small `TUNGSTEN_FVG.mq4` (bull gap = `low[0] > high[2]`, bear gap = `high[0] < low[2]`). Everything else skipped.

---

## 2. Per-indicator build contract

Each forged `.mq4` must:
- Declare exact `#property indicator_buffers` / `indicator_separate_window|chart_window`.
- Query symbol properties at init (`Point`, `Digits`, `MarketInfo`) — no hard-coded gold constants; instrument-relative throughout (ATR units).
- Bound every historical loop by `Bars`; guard every divide; handle `iATR/iMA` returning 0 on unbuilt history with an abstain fallback.
- Expose a stable public buffer interface documented in a header comment (buffer index → meaning), because the EA reads these by index via `iCustom`.
- Be deterministic and lookahead-free: no future-bar index in any series feeding a live buffer.

---

## 3. Unified scoring integration contract (the bounded-threshold law)

- **3.1** Each indicator maps to a **sub-score** in a fixed closed interval — direction sub-scores in `[-1, +1]`, magnitude/conviction sub-scores in `[0, 1]`.
- **3.2** Sub-scores enter TUNGSTEN's existing IC-weighted CEUS combiner as new weighted votes. Weights are learned online (per-regime IC), same mechanism as native layers — no privileged hard weight.
- **3.3** The combined pre-clamp score is normalized by total active weight so adding indicators can't inflate the scale.
- **3.4** Final unified conviction is **clamped to `[SCORE_MIN, SCORE_MAX]`** (the existing CEUS scale). It may asymptotically approach but never reach or exceed the bound — enforce with a saturating map (e.g. clamp after a `tanh`-style squash), so no combination of maxed sub-scores can breach the ceiling or floor.
- **3.5** No single indicator's sub-score may exceed a per-component cap (e.g. ≤ X% of total possible weight) so one layer can never unilaterally trip an entry. "Possible but bounded" — every layer *can* contribute meaningfully, none *can* dominate.
- **3.6** Abstain propagation: an abstaining indicator contributes zero weight (not a zero vote that drags the mean). Combiner renormalizes over present layers only.

---

## 4. Definition of done (agent may not report complete until all true)

1. F1–F4 (+ optional F5-wiring, F6-FVG) exist as original `.mq4`, clean-room verified.
2. Each compiles zero-error/zero-warning in MetaEditor.
3. Each deployed to the correct `MQL4\` subpath; EA `iCustom` calls reference exact filenames and correct buffer indices.
4. Sub-scores wired into CEUS; unified score provably respects `[MIN,MAX]` and the per-component cap under a max-input stress test.
5. No existing TUNGSTEN path regressed; full EA still compiles clean.
6. A decision using the new layers is reconstructable from logs (which layer voted what, at what weight).

---

## 6. Root-Cause Calibration Pass (collective, whole-algorithm)

*This pass falls under Forge Sword. Its target is not symptoms but causes. The base carries ~2,990 calibration/phase references and a long trail of "warrant" patches — evidence of fix-on-fix. The mandate is to end that pattern: fix each root once, guard it forever, and drive the recurrence rate down monotonically with every run.*

### 6.1 Diagnose before touching
For every calibration-phase defect (Phases 1, 2, 3A–3E, 4, 5, 6, CATREC, INDINTEL), classify the **root cause** into exactly one of:
- **Insufficient evidence** — decision made on too few trades/samples (n below significance floor).
- **Mathematical error** — wrong formula, precedence, sign, normalization, or statistical method (e.g. unsigned IC where signed was needed).
- **Misaligned logic** — phase-to-phase handoff mismatch, threshold re-tested against stale data, holdout leak, seam incoherence.
- **Indicator non-use / mis-association** — an available signal not fed where it would help, or a spurious association formed from noise.
- **Timing / budget** — phase failing open on timeout, checkpoint wiping valid estimates, ordering dependency.
- **Dead / unreachable path** — a fix that never executes in production (the `g_CalibSilent` class).

A defect is not "fixed" until its class is named and the fix addresses *that class*, not the visible symptom.

### 6.2 Fix the fix
Where a prior warrant patched a symptom, trace to the origin and repair there. Remove the now-redundant patch in the same change (forward-only, §0.5) rather than leaving compensating layers that will themselves rot. If two patches encode contradictory assumptions, that contradiction is the root — resolve it once.

### 6.3 Regression guard per root (the convergence mechanism)
Every root fixed gets a permanent guard: an assertion, invariant, or self-test that makes that entire class **unable to recur silently**. This is what makes "more runs → fewer problems" mathematically true rather than hopeful — each pass permanently retires a class, so the residual defect surface shrinks monotonically and never re-expands. The guard lives in the acceptance harness (Prometheus, §5).

### 6.4 Every line accountable
The pass is whole-algorithm, not phase-local. Each line touching calibration, scoring, learning, or execution is checked against: is its evidence sufficient, its math correct, its logic aligned with neighbors, its indicators used where they'd help, its path reachable? Findings logged per line-region with root class and fix.

### 6.5 Bounded-benefit adaptation (win-win under limits)
"Strive for perfection with all limits in mind, adapting to them beneficially." Operationalized: every calibrated parameter seeks its optimum **within** its hard `[min,max,max-step]` guardrail (from the requirements spec §1.5). The objective is the risk-adjusted one already in use (WR × PF × log n), never raw return. Adaptation may improve the parameter but may never trade a safety bound for a performance gain — the "win-win" is optimum-within-limits, never optimum-past-limits.

### 6.6 Convergence report
Each pass emits: defects found, root class distribution, roots retired (with their new guards), residual open items, and the measured trend in recurrence rate across passes. The success metric is that this rate falls run over run and no retired class reappears. Perfection is the asymptote, not the claim.

---

## 5. Interlock with Prometheus / existing agents

Forge Sword owns **indicator forging + wiring**. It hands finished, compile-clean, wired artifacts to Prometheus (or the correctness-pass agent), which runs them against the **TUNGSTEN_QUANT_REQUIREMENTS** acceptance harness (§9.4 correctness pass, fault injection, lookahead audit). Nothing forged goes live until it clears that harness. Two agents, one contract, no blind merges.
