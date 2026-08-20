# FORGE SWORD — Executable Annex (Spec Hardening)
### The precision layer: what makes the spec executable without interpretation
*Companion to FORGE_SWORD_agent.md, TUNGSTEN_QUANT_REQUIREMENTS.md, TUNGSTEN_MARKET_READY_THESIS.md. Base: 10.30 A7.5 SLS(116). Where a value is a calibration output rather than a fixed constant, it is marked `⟨CALIB⟩` — the agent fills it from validated calibration, never guesses it.*

*Status honesty: this annex closes every ambiguity gap identifiable from the current codebase. It is complete enough to execute against with no interpretation. It remains a living document — the build will surface refinements, and those are folded back here rather than pretended away.*

---

## A. Parameter & constant registry (single source of truth)

Every tunable lives here with type, bound, step, and origin. No magic numbers anywhere else in the codebase — all reference this registry.

| Symbol | Meaning | Type | Bound `[min,max]` | Max step/update | Origin |
|---|---|---|---|---|---|
| `SCORE_MIN` / `SCORE_MAX` | Unified CEUS conviction bounds | double | match existing CEUS scale | — | fixed |
| `COMP_CAP` | Max share of total weight any one layer may hold | double | `[0.10, 0.30]` | 0.02 | fixed policy |
| `SIG_FLOOR_N` | Min sample count before a learned cell influences live | int | `[30, 200]` | — | fixed policy |
| `IC_HALFLIFE` | Decay half-life for online IC/EMA memory | bars | `⟨CALIB⟩` | bounded | Phase 2 |
| `RR_MIN` | Min reward:risk | double | `1.5` fixed | — | fixed (Phase 3C invariant) |
| `KELLY_FRAC_MAX` | Kelly cap | double | `0.50` fixed | — | fixed |
| `RISK_PER_TRADE` | % equity at risk/trade | double | `⟨CALIB⟩ ≤ hard cap` | bounded | risk policy |
| `DAILY_LOSS_HALT` | Daily DD halt threshold | double | fixed policy | — | risk policy |
| `CONSEC_LOSS_BRK` | Consecutive-loss breaker count | int | fixed policy | — | risk policy |
| `EQUITY_FLOOR` | Absolute kill-switch equity | double | fixed policy | — | risk policy |
| `SPREAD_CEIL_ATR` | Max spread as ATR fraction to allow entry | double | `⟨CALIB⟩` | bounded | Phase 3A |
| `MAX_CALIB_MIN` | Calibration time budget | min | `[30, 90]` | — | budget |
| `TICK_BUDGET_MS` | Max compute per tick | ms | see §F | — | budget |

Rule: a `⟨CALIB⟩` value is never hard-typed into logic; it is read from the calibrated parameter block, which itself passed §I acceptance.

---

## B. Interface contracts — forged indicators

Each `iCustom` consumer in the EA binds to these exact signatures and buffer indices. Change the indicator, change every consumer in the same commit (§0.5).

**F1 `TUNGSTEN_LPOC`** — inputs `(lookback, fadeBars, profileWindow)`
- buf 0 `SweepDir` ∈ {-1,0,+1}
- buf 1 `POC_Price` (price)
- buf 2 `DistToPOC_ATR` (double, ATR units)
- abstain value: `SweepDir=0`, `DistToPOC_ATR=EMPTY_VALUE`

**F2 `TUNGSTEN_WOSC`** — inputs `(fastEMA, slowEMA, smooth, wTrend, wMR, wMom)`
- buf 0 `Osc` ∈ [-1,+1]
- buf 1 `Signal` ∈ [-1,+1]
- abstain: both `0`

**F3 `TUNGSTEN_ATT`** — inputs `(fastLen,fastMult, midLen,midMult, slowLen,slowMult)`
- buf 0 `TrendState` ∈ {-1,0,+1} (agreement of 3)
- buf 1 `FastTrail`, buf 2 `MidTrail`, buf 3 `SlowTrail` (prices)
- abstain: `TrendState=0`

**F4 `TUNGSTEN_MS`** — inputs `(pivotSens, zoneLookback)`
- buf 0 `StructBreak` ∈ {-2,-1,0,+1,+2} (±2 BOS, ±1 CHoCH)
- buf 1 `NearestOB_Price`, buf 2 `PDH`, buf 3 `PDL`
- abstain: `StructBreak=0`, prices `EMPTY_VALUE`

**Common contract:** every buffer either returns a valid value or the documented abstain sentinel; consumers treat abstain as zero-weight (§3.6), never as a directional zero.

---

## C. Calibration pipeline — dependency & read/write contract

The historical bug source was phase-to-phase incoherence (stale threshold re-tests, holdout leaks, order dependence). This pins the DAG. Each phase declares what it **reads** and **writes**; no phase may read a value a later phase writes.

```
RunPhase0SystemChecks            [reads: env, symbol props | writes: readiness flags]
  → RunIndicatorIntelligence     [reads: history, F1–F4 | writes: per-indicator IC seeds]
  → RunFeatureSignalDiagnostic   [reads: IC seeds        | writes: feature viability]
  → Phase2 RegimeMultiConfig     [reads: history         | writes: 9-regime IC (SIGNED)]
  → Phase2_2 PerRegimeRefinement [reads: regime IC       | writes: refined per-regime]
  → Phase3A ExitHorizon/MAE      [reads: regime          | writes: exit horizons, noise floor]
  → Phase3B ComponentWeights     [reads: 3A, holdout70/30| writes: weight vector/regime]
  → Phase3C TPSL                 [reads: 3A,3B           | writes: SL/TP mult (RR_MIN guard)]
  → Phase3D/E dwell/fingerprint  [reads: 3B/3C          | writes: additive only]
  → Phase4 BuildProbabilityDB    [reads: all above       | writes: 6D ProbDB (read-only after)]
  → Phase5 GhostRegimeTPSL       [reads: ProbDB          | writes: ghost results]
  → Phase6 UnlimitedOOSGhost     [reads: chronological   | writes: p6Met, quarantine set]
  → RunComprehensiveGhostValidation → RunPreFlightGates  [reads: all | writes: GO/NO-GO]
```

**Hard rules:**
- C1 — **One holdout split convention** (70/30) used identically by every phase that holds out. No phase re-tests a threshold another already fit on the same in-sample data.
- C2 — **ProbDB is read-only** after Phase 4 for the rest of the run. Any write attempt post-build is a defect.
- C3 — **Every phase fails open on timeout** (budget §A) and logs the truncation; a truncated phase must not write partial results that look complete.
- C4 — **Signed IC** where sign carries meaning (the documented Phase 2 fix); never unsigned where direction matters.
- C5 — **No reversed-direction lookahead loop** touches a live threshold (the SLS21 class); every historical loop indexes past→present.

---

## D. Numerical policy

- D1 — Every division guarded: denominator checked `> EPS` (define `EPS=1e-9` for ratios, `Point/2` for price deltas) else abstain.
- D2 — `iATR/iMA/iMACD/iRSI/iADX` return 0 on unbuilt history → treated as abstain, never as a real 0 reading.
- D3 — NaN/Inf policy: any computed value tested with `MathIsValidNumber`; invalid → abstain + log, never propagated into scoring or an order.
- D4 — All price math instrument-relative (ATR units / Point), never raw pips.
- D5 — Rounding to `Digits` only at the order boundary, not mid-calculation.

---

## E. State schema, checkpoint & rollback

- E1 — State file carries `schemaVersion`. Loader migrates known older versions or safely rejects and cold-starts (never mis-parses).
- E2 — Atomic writes: temp + rename (existing pattern). No partial state visible.
- E3 — **Checkpoint before each learning update**; keep last N=3 good checkpoints.
- E4 — **Auto-rollback trigger:** if post-update live expectancy degrades past tolerance within the watch window (§ requirements 1.6), restore last good checkpoint and log the rollback with cause.
- E5 — Checkpoint/resume of a long phase (Phase 3B outer loop) must never overwrite valid estimates with partials (documented past bug) — resume merges, does not clobber.

---

## F. Performance budget

- F1 — Full 14-layer + F1–F4 + ProbDB lookup completes within `TICK_BUDGET_MS` on new-bar events; between bars, cached.
- F2 — Heavy recomputation gated to new-bar (`Volume[0]==1` / time change), never per-tick.
- F3 — Calibration respects `MAX_CALIB_MIN`; `Sleep(1)` per ~1000 combinations to keep terminal responsive (existing cadence).
- F4 — No unbounded loop: every historical scan bounded by `Bars` and by an explicit max-lookback.

---

## G. Failure Modes & Effects (FMEA) — the abstain/halt map

| # | Failure mode | Detection | Effect enforced |
|---|---|---|---|
| G1 | Insufficient history at start | `Bars < needed` | Abstain all layers; no entries until satisfied |
| G2 | Indicator returns 0/invalid | D2/D3 | Layer abstains, zero weight |
| G3 | Spread > ceiling | `SPREAD_CEIL_ATR` | Reject/re-price entry |
| G4 | Order error (requote, off-quotes, no money) | error-code branch | Bounded gate-specific retry, then abstain + log |
| G5 | Learned cell below `SIG_FLOOR_N` | sample count | Fall back to hard-coded prior |
| G6 | Regime uncertain (no majority belief) | distribution sharpness | Reduce size or stand down |
| G7 | Drift detected | CUSUM/rolling WR | Reduce size → quarantine regime |
| G8 | Daily loss / consec-loss / equity floor | risk counters | Halt new entries / kill switch |
| G9 | State corrupt / schema mismatch | E1 | Cold-start safe; alert |
| G10 | Calibration timeout | budget | Fail open, log truncation, use last good |
| G11 | Re-entrancy / lock leak | guaranteed-release pattern | Lock always released on every return path |
| G12 | NaN/Inf in scoring | D3 | Value dropped, decision abstains |

Every mode has exactly one enforced effect; none is left to incidental behaviour.

---

## H. Logging schema (per decision)

One structured record per evaluated bar/trade, sufficient to replay offline (requirements §8.3):
`ts, regime, regimeBelief[9], layerVotes[…], F1..F4 subscores, activeWeights[…], preClampScore, unifiedScore, gateResults{margin,spread,news,risk}, decision{enter/skip/reason}, orderResult?, riskState{dailyPnL,consecLoss,equity}`
- H1 — Reason-for-skip is mandatory on every non-entry.
- H2 — Every safety event (G3,G7,G8,G9,G10,G11) emits an alert-level line.
- H3 — Self-audit summary on schedule: active regime, live-vs-expected, quarantine list, parameter drift, open risk.

---

## I. Acceptance test matrix (must all pass before GO)

| ID | Test | Pass criterion |
|---|---|---|
| T1 | Compile | Zero errors, zero warnings, MetaEditor |
| T2 | Indicator wiring | Each `iCustom` binds correct file + buffer index; abstain sentinels honoured |
| T3 | Bounded score stress | All sub-scores maxed → unified ∈ (SCORE_MIN,SCORE_MAX), never equal/exceed; no single layer > `COMP_CAP` |
| T4 | Invariant fuzz | 10⁴ randomized bars: SL always set/correct side, `TP≥SL×RR_MIN`, lock always released |
| T5 | Fault injection | Inject G1–G12 each → enforced effect observed, no blind trade |
| T6 | Lookahead audit | No live threshold reads a future bar (static + runtime check) |
| T7 | Reachability | Every calibration/learning branch provably executes in production (no `g_CalibSilent` dead path) |
| T8 | Phase DAG | Read/write contract (§C) holds; no stale re-fit; ProbDB read-only post-build |
| T9 | Degradation halt | Synthetic decay → drift detected → quarantine → stand-down, automatically |
| T10 | Rollback | Forced bad update → auto-restore last good checkpoint |
| T11 | Replay | A random decision fully reconstructable from logs alone |
| T12 | Budget | Tick compute ≤ `TICK_BUDGET_MS`; calibration ≤ `MAX_CALIB_MIN` |

---

## J. Traceability map (requirement → code → guard → test)

Every requirement resolves to a code region, a permanent guard, and the test that proves it. Sample rows; the agent completes the full table as it forges.

| Requirement | Code region | Guard | Test |
|---|---|---|---|
| Bounded unified score (§3.1–3.5) | CEUS combiner | clamp-after-squash + `COMP_CAP` assert | T3 |
| SL/TP integrity (§4.3) | order send path | runtime invariant assert | T4 |
| Abstain propagation (§3.6) | combiner renorm | sentinel check | T2 |
| Signed IC (Phase 2, C4) | RunPhase2* | sign-preservation assert | T8 |
| No lookahead (C5) | all hist loops | index-direction check | T6 |
| Lock release (G11) | OnTick guard | guaranteed-release pattern | T4/T5 |
| Drift stand-down (§6) | monitor layer | degradation halt | T9 |

---

## K. Sign-off checklist (one page, all-or-nothing)

Nothing goes live until every box is true:
- ☐ T1–T12 all pass
- ☐ Parameter registry (§A) complete; no magic numbers outside it; all `⟨CALIB⟩` filled from validated calibration
- ☐ Interface contracts (§B) bound exactly in every consumer
- ☐ Phase DAG (§C) verified; C1–C5 hold
- ☐ FMEA (§G) — every mode maps to its enforced effect
- ☐ Traceability table (§J) complete: every requirement → guard → passing test
- ☐ Root-cause pass: each defect classed, fixed at origin, old patch removed, guard installed
- ☐ Convergence report shows recurrence rate down vs prior pass; no retired class reappeared
- ☐ Full EA still compiles clean; no prior path regressed

---

### What "ultimate" honestly means for this spec
This annex removes interpretation: an agent can execute it without guessing, and every claim is tied to a test. That is the achievable form of "ultimate" for a specification — **complete, unambiguous, and self-proving.** The form it can never take is "final and beyond revision," because the build will teach us things and this document absorbs them. A spec that stops changing has stopped being read. This one is built to keep earning the word, run after run — which is the same discipline the system itself runs on.
