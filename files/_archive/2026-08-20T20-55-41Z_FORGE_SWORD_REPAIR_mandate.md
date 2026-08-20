# FORGE SWORD REPAIR — Agent Mandate
### Whole-algorithm reasoning pass: find every weak link, reason through alternatives, overhaul as a unit
*Base: TUNGSTEN 10.41 A7.5 QUANT_SLS(127) — current head. This pass is exhaustive and forward-only. Every change must leave the system more capable than it found it, and every change must be in sync with every other.*

---

## 0. Prime law — this agent is the one that finishes the job

This is not a patch run. This is not incremental. This is the pass that takes TUNGSTEN from "still fixing things" to "producing real-world decisions." The agent that executes this mandate must treat it as the most important engineering task it will ever run. Every weak link found is a weak link that, if left, will cost real money or require another return trip. There are no more return trips after this one.

**The method, for every logic in the algorithm:**
1. **Identify** — is this logic sound, weak, misaligned, underperforming, dead, or limited?
2. **Reason** — if not sound: generate at minimum three mathematically grounded alternatives. State the trade-offs of each explicitly. No hand-waving — show the math, show the edge cases, show the failure mode of each option.
3. **Select** — choose the alternative that best serves the system *as a whole*, not just the local function. Justify in writing.
4. **Implement** — write the code. Clean, bounded, guarded, instrument-relative.
5. **Sync** — update every consumer, every neighbour, every downstream dependency. The system moves as a **unit**. A change that improves one subsystem while degrading another is not an improvement — it is a new bug.
6. **Verify** — prove the change compiles clean, passes its invariants, and doesn't regress anything.

**Completeness mandate:** not a single function, phase, data path, or code region may be left unexamined. The agent scans everything. If a logic is sound, it says so in one line and moves on. If it is weak in any way, it stops and does the full six-step work. The convergence report at the end must account for every region — what was examined, what was sound, what was changed, and what the change achieved. A region not in the report is a region that was missed, and that is a failure of this mandate.

**Dead code mandate:** every dead, orphaned, gated-off, or unreachable function is either (a) resurrected as a fully wired, working, adaptive component that makes the system stronger, or (b) deleted entirely with its declaration, forward-decl, and every comment referencing it removed. There is no third option. Dead code that "might be useful someday" is dead weight that makes the codebase harder to reason about, harder to maintain, and more likely to hide bugs. The bar for resurrection is high: the function must solve a real problem the system currently has, and must be wired end-to-end with tests. The bar for deletion is simple: if it doesn't clear the resurrection bar, it goes. (See §1D for the specific dead-code inventory.)

**Quality standard:** this agent runs alongside Forge Sword proper. Its output must be at least as rigorous as any prior warrant pass. Every change compiles zero/zero. Every change is traceable. Every change makes the system more capable, never less. The measure of success is not volume of changes — it is how close to completion the system is when this pass ends.

---

## 1D. DEAD CODE — resurrect or delete, no middle ground

The codebase carries orphaned functions, gated-off features, and unreachable paths. Each is resolved below. The agent must handle every one in this pass.

**RESURRECT — these solve real current problems:**

| Function | What it does | Why it matters now | Resurrection target |
|---|---|---|---|
| `CalculateKellyCeiling()` (ln 44885) | Full Kelly with asymmetric payoff, drawdown-scaled | The system needs regime-conditioned Kelly sizing (§4B). This function already computes it. | Wire into `OptimizePrecisionLotSize` as the sizing authority. Feed it the unified scorer's edge estimate and the regime's realised reward:risk. Verify the ½-Kelly cap and drawdown scaling are in place. |
| `CanTakeAnotherTrade()` (ln 25774) | Hourly trade frequency gate | Prevents over-trading in choppy regimes. Currently orphaned — the system has no active frequency cap per hour. | Wire into `RunPreFlightGates` as a pre-entry check. Make the hourly cap regime-aware (tighter in Choppy/Noise, wider in Strong Trend). |
| `GetCurrentThreshold()` (ln 28533) | Hour-based threshold adjustment | Session-aware entry selectivity — tighter thresholds in low-edge hours. | Wire into the entry gate alongside `GetLearnedOptimalThreshold`. The two must compose (learned threshold + hour adjustment), not compete. |
| `IsCurrentHourDisabled()` (ln 28491) | Hour-based session filter | Works with the session performance system. | Wire as a soft gate: disabled hours increase threshold rather than hard-blocking (the existing comment says "increased selectivity, not disabled" — honour that intent). |
| `LE_ComputeBracketTP()` (ln 38492) | Bracket TP from living-edge + dwell data | Adaptive take-profit using actual regime dwell statistics. Currently orphaned despite being built in WARRANT#36. | Wire into the TP computation path. The bracket TP must compete with the calibrated TP and the winner is selected per-regime based on which has better historical PF. |
| `LE_AvgDwell()` (ln 38446) | Average dwell time per regime cell | Feeds `LE_ComputeBracketTP` and optimal stopping. | Resurrect as a dependency of the bracket TP path above. |
| `CalculateIntelligentRisk()` (ln 25114) | Periodic risk recalculation | Was previously destructive (reset state every 5 trades — the comment documents the bug). The *concept* is right: periodic risk reassessment. | Rewrite from scratch as a non-destructive periodic risk audit: every N trades, re-evaluate current risk exposure against the regime's expected edge. If exposure exceeds what the edge justifies, trim. Never reset state — read-only assessment with a sizing recommendation. |
| `GetRejectReasonText()` (ln 12040) | Human-readable rejection reasons | Decision reconstructability — currently the system rejects entries without always logging *why* in readable form. | Wire into the structured decision log (§5C). Every rejection emits a reason code AND this function's human-readable text. |

**DELETE — these don't clear the resurrection bar:**

| Function | Why delete |
|---|---|
| `PrintEmpathetic()` (ln 12994) | Cosmetic logging wrapper. Adds no signal, no safety, no capability. Delete function + all refs. |
| `CheckMilestones()` (ln 22303) | Balance celebration messages. Not a trading function. If wanted as a user-facing feature, move to a separate utility file — it does not belong in the EA's critical path. Delete from main EA. |
| `IsBuffaloSetup()` (ln 23034) | Hard-coded "score >= 70 = premium opportunity" with multi-position scaling. This is exactly the kind of unguarded conviction amplification the bounded-scoring contract (§1B) exists to prevent. The concept (high-conviction = scale up) is already handled by Kelly sizing. Delete. |

**`g_CalibSilent` — the structural dead-code generator:**
This flag gates ~40+ `Print`/`TLog` calls throughout calibration. When `true`, entire calibration narration branches are skipped — but more critically, it historically gated *logic* branches too (the SLS21 finding). The flag must be audited: every `if(!g_CalibSilent)` block is checked for whether it contains logic or just logging. Logic blocks are ungated (they must always run). Logging blocks are converted to TLog (which respects log level) and the `g_CalibSilent` check is removed. The flag itself is then deleted — logging verbosity is controlled by log level, not by a global boolean that can accidentally gate logic.

---

## 1. SCORING ENGINE — unify, bound, make every vote honest

### 1A. Dual scorer elimination
**Target:** `CalculateScoreWithWeights()` (line ~6023) vs `CalculateEnhancedUnifiedScore()` — two scorers, two ranking behaviours, calibration uses one and live uses the other.
**Reasoning required:** Why do two exist? What does the simplified one compute that the enhanced one doesn't? Is there any diagnostic value worth preserving, or is it pure legacy?
**Action:** Unify to one scorer on every path — calibration, ghost, live. If the simplified scorer captures a useful diagnostic (e.g. raw component agreement count), extract that as a diagnostic-only side output, not an alternative ranking. Every call site in the file must resolve to one function.
**Sync check:** `MeasureComponentSensitivity`, Stage -1 isolation scan, `SelfCalibrateConvictionEngine` — all must call the same scorer.

### 1B. Bounded unified score integrity
**Target:** The CEUS combiner, all trim functions (`ComputeSoftMembershipEntropyTrim`, `ComputeEnsembleConeTrim`, `ComputeLivingEdgeInversionTrim`, `ComputeRelationshipDisagreementTrim`, `ComputeMultiTFCoherenceTrim`), and the new F1–F4 sub-scores.
**Reasoning required:** Do the trims stack multiplicatively or additively? Can a pathological combination of trims zero out a strong signal or amplify a weak one past the ceiling? What is the worst-case output under adversarial inputs?
**Action:** Prove that the final unified score is bounded `[SCORE_MIN, SCORE_MAX]` under every combination of inputs. If it can breach, add the saturating clamp (tanh-squash before hard clamp). Verify the per-component cap (`COMP_CAP`) holds — no single layer dominates.
**Sync check:** Every consumer of the unified score (entry gate, sizing, ProbDB lookup) must expect the same scale.

### 1C. Conviction margin gate
**Target:** `GetLearnedOptimalThreshold()` and the entry gate that checks `|score| >= threshold`.
**Reasoning required:** Is the threshold learned on the same scorer that produces the live score? (If dual-scorer existed, this may have been learned on the wrong one.) Is the margin regime-aware? Does it account for the current regime's expected IC?
**Action:** Threshold must be learned and applied on the unified scorer. Margin must scale with regime confidence — high-confidence regime → tighter margin acceptable; low-confidence → wider margin required. Implement if not already present.

---

## 2. CALIBRATION PIPELINE — every phase honest, every handoff clean

### 2A. Phase DAG integrity
**Target:** The full pipeline: `RunPhase0SystemChecks` → `RunIndicatorIntelligence` → `RunFeatureSignalDiagnostic` → `RunPhase2_1_RegimeMultiConfig` → `RunPhase2_2_PerRegimeRefinement` → `OptimizeSessionWeightsPerRegime` → `OptimizeVolatilityWeightsPerRegime` → `OptimizeTPSLForWinRate` → `OptimizeTPSLMultipliersPerRegime` → `OptimizeExitHorizonPerRegime` → `OptimizeComponentWeightsForRegime`/`Soft` → `BuildProbabilityDatabase`/`MultiDimensional` → `RunComprehensiveGhostValidation` → `RunPreFlightGates`.
**Reasoning required:** For each phase: what does it read? What does it write? Can any phase read a value that a later phase is responsible for writing? Can any phase re-test a threshold on data that overlaps with an earlier phase's holdout?
**Action:** Enforce one global 70/30 chronological holdout. Add a read/write declaration comment at the top of every phase function. Add a runtime assertion that ProbDB is read-only after `BuildProbabilityDatabase` completes. Trace and fix any holdout contamination.

### 2B. INDINTEL raw-return vs simulated-outcome (WARRANT#136/#145)
**Target:** `RunIndicatorIntelligence` and the IC ranking it produces.
**Reasoning required:** WARRANT#145 claims to be the "real architectural fix." Verify: does INDINTEL now rank by simulated TP/SL outcome? Or does it still rank by raw return with a downstream trim? If the latter, the fix is a patch, not a resolution.
**Action:** INDINTEL must rank indicators by the metric that matches the live execution — simulated outcome under actual TP/SL. Raw return is a diagnostic, not an authority. If #145 achieved this, confirm and move on. If not, implement it.

### 2C. Sparse regime strategy
**Target:** Regimes r3 (Bullish Reversal), r4 (Bearish Reversal), r5 (Range), r6 (Choppy), r7 (Noise), r8 (Building Momentum) — all flatlined at val=0.0% in the live run.
**Reasoning required:** Three alternative approaches, each with trade-offs:
  (a) **Cross-instrument transfer** — calibrate on instruments where these regimes are common (e.g. Range on USDJPY, Choppy on EURUSD during Asia), transfer with a discount. Pro: real evidence. Con: cross-instrument IC may not transfer.
  (b) **Multi-timeframe pooling** — aggregate regime samples across M5/M15/H1 to increase N. Pro: same instrument. Con: regime dynamics may differ across timeframes.
  (c) **Honest stand-down** — if N < floor, the regime is marked `UNQUALIFIED` and the system does not trade in it, period. Pro: never trades on a guess. Con: misses opportunity in rare regimes that may have edge.
**Action:** Implement (c) as the safety floor — `UNQUALIFIED` regimes hard-stand-down. Then layer (a) or (b) as an optional evidence-gathering mechanism that can promote a regime from `UNQUALIFIED` to `QUALIFIED` once its N crosses the significance floor. The sparse-seed fallback (lines ~5338–5351) is retired — no more trading on a guess.

### 2D. Calibration timeout behaviour
**Target:** Every phase with a time budget.
**Reasoning required:** What happens when a phase truncates? Does it write partial results? Does it mark them as partial?
**Action:** Truncated results must carry a `TRUNCATED` flag. Downstream phases that consume a truncated input must either (a) fall back to last-good values, or (b) propagate the truncation and fail open. No truncated value may be consumed as if it were complete.

### 2E. Checkpoint/resume integrity
**Target:** State save/load around P3B and long phases.
**Action:** Verify that resume merges, not clobbers. Add: restored state must be at least as complete as pre-crash state (checksum or field count). Keep last 3 good checkpoints.

---

## 3. REGIME INTELLIGENCE — make the classifier and its consumers honest

### 3A. Regime classifier confidence
**Target:** `DetectCurrentRegime()`, `ClassifyBarToRegime()`, `g_RegimeScores[9]`, `g_RegimeConfidence[9]`.
**Reasoning required:** Does the classifier output a belief distribution or a single label? If single label, what happens at regime boundaries where two regimes score similarly? Does hysteresis (`g_RegimeHysteresisInitialized`) prevent flip-flopping but also prevent honest regime changes?
**Action:** The classifier must output a distribution. When no regime holds clear majority (Shannon entropy of distribution > threshold), the system enters `UNCERTAIN` state → reduce size or stand down. Hysteresis is acceptable for preventing noise-driven flips but must not delay a genuine regime change by more than N bars.

### 3B. Regime transition hostility
**Target:** The regime transition matrix and the R6/R7 trim logic.
**Reasoning required:** Does the system currently trade the transition probability, or only react after the regime has already changed? If the latter, the system is always late.
**Action:** Maintain a transition probability matrix. When the current regime's most-likely next state is historically hostile to the open direction, pre-emptively trim conviction. The trim should be proportional to the transition probability, not binary.

### 3C. Quarantine and re-promotion
**Target:** `g_RegimeQuarantineTrades[9]` and the quarantine/re-promotion logic.
**Reasoning required:** What triggers quarantine? What triggers re-promotion? Is re-promotion too easy (a small rebound) or too hard (never recovers)?
**Action:** Quarantine triggers on drift detection (CUSUM/rolling WR below floor). Re-promotion requires the same OOS gauntlet a new regime faces — p6Met ≥ 3/6, WR ≥ floor, minimum N. No shortcut on a lucky streak.

---

## 4. RISK & EXECUTION — every order safe, every exit deterministic

### 4A. Order send hardening
**Target:** `SafeOrderSend()` (line ~1272), `SafeOrderClose()` (line ~1266).
**Reasoning required:** Does every MT4 error code have an explicit handler? Are retries bounded and gate-specific? Does a failed modify leave the position without a stop?
**Action:** Audit every error code path. No position may exist without a stop for more than one tick. Failed modify → immediate re-attempt; second failure → emergency close. Retries bounded (max 3), with re-quote handling.

### 4B. Sizing integrity
**Target:** `OptimizePrecisionLotSize()`, the Kelly fraction, and `RISK_PER_TRADE`.
**Reasoning required:** Is the Kelly fraction computed from the unified scorer's edge estimate, or from a different source? Is the edge estimate regime-conditioned? Does the floor/ceiling apply after Kelly or before?
**Action:** Kelly input = regime-conditioned edge estimate from the unified scorer. Fraction capped at 0.5. Result clamped to `[min_lot, max_risk_%_of_equity]`. Unknown edge (insufficient evidence) → minimum lot.

### 4C. Spread/cost calibration
**Target:** The "spread not yet calibrated this run — COST-UNVALIDATED" path.
**Reasoning required:** The current approach blocks or allows entries without cost validation during the calibration window. Neither is ideal.
**Action:** Seed spread estimate from the events CSV (known high-impact windows get widened ceiling) and from `MarketInfo(MODE_SPREAD)` at init. Refine online. Hard-block entries until a minimum sample (50 ticks) is gathered. Regime-aware spread ceiling: news windows auto-tighten.

---

## 5. OBSERVABILITY — see everything, miss nothing

### 5A. Log overwrite → append
**Target:** `TLog()` (line ~7199), specifically `FileOpen("TUNGSTEN_live.log", FILE_WRITE|FILE_TXT|FILE_SHARE_READ)`.
**Action:** Change to append pattern. Options: (a) `FILE_READ|FILE_WRITE` with `FileSeek(handle, 0, SEEK_END)` before write, (b) accumulate in a global string buffer and flush once per bar, (c) rolling log with size cap. Implement (a) as the simplest correct fix. Add (c) as a guard against unbounded growth (rotate at e.g. 2MB, keep last 2 files).

### 5B. Silent progress gaps — structural guard
**Target:** Every CPU-bound loop in the codebase.
**Reasoning required:** The pattern has recurred at 4+ call sites (WARRANT#20, #134, #141, and the new 6-minute gap post-P3B). Reactive TLog additions at individual sites will keep recurring.
**Action:** Identify every loop that iterates > 1000 times or runs > 5 seconds. Add a progress TLog at a fixed interval (every 30 seconds or every 10% of expected iterations). This is a one-time exhaustive audit, not a per-discovery patch.

### 5C. Structured decision log
**Target:** The per-bar/per-trade decision record (requirements §8.3, WARRANT#137).
**Reasoning required:** Is the current logging sufficient to replay any decision offline? Does it include: regime belief distribution, all layer votes, all trim values, the unified score, gate outcomes, and reason-for-skip?
**Action:** Verify completeness against the schema in the executable annex (§H). Any missing field is added. The structured log is separate from the human-readable TLog — it appends always, never rotates away active-session data.

---

## 6. LEARNING & ADAPTATION — flexible but never past a limit

### 6A. Online IC / weight nudging bounds
**Target:** `g_OWA_NudgeWeights[9][6]`, `g_MCM_Weights[4][9][6]`, and the online learning paths.
**Reasoning required:** Are nudge weights bounded per update step? Can accumulated nudges drift a weight past its `[min, max]`? Is there a rollback trigger if post-nudge performance degrades?
**Action:** Every nudge clamped to `max_step_per_update`. Accumulated weight clamped to `[min, max]`. Post-update watch window: if expectancy degrades past tolerance, auto-rollback to last good checkpoint (§2E).

### 6B. ProbDB staleness
**Target:** `BuildProbabilityDatabase` / `BuildMultiDimensionalProbabilityDatabase`, and the read-only-after-build rule.
**Reasoning required:** How old can the ProbDB be before it's stale? Is there a mechanism to rebuild periodically, or does it persist from the first calibration indefinitely?
**Action:** ProbDB carries a build timestamp and a bar-count-at-build. If current bars exceed build-bars by more than a threshold (e.g. 20%), flag as stale and schedule a rebuild at the next new-bar event. Stale ProbDB → reduce its authority (discount its output) until rebuilt.

### 6C. Ghost/OOS validation honesty
**Target:** `RunComprehensiveGhostValidation`, the p6Met criterion, and the ghost evaluation engine.
**Reasoning required:** Is the ghost evaluation truly out-of-sample? Does it use chronological ordering? Can any in-sample bar leak into the ghost set? Is the ghost set large enough to be statistically meaningful?
**Action:** Verify chronological, non-overlapping, unlimited-OOS ghost evaluation. Minimum ghost set size = 50 trades or stand down. p6Met ≥ 3/6 required for promotion. Any bar that appeared in any training set is excluded from ghost evaluation — add an assertion.

---

## 7. INDICATOR & SIGNAL CHAIN — every wire correct, every abstain honest

### 7A. F1–F4 wiring verification
**Target:** WARRANT#135's integration of the forged indicators.
**Action:** Verify: (a) each `iCustom` call references the correct filename and buffer index per the interface contract (annex §B), (b) abstain sentinels are checked and result in zero-weight (not zero-vote), (c) the reliability curve is building correctly even though it's "not yet calibrated."

### 7B. Native indicator guards
**Target:** All ~498 `iATR`/`iMA`/`iMACD`/`iRSI`/`iADX` call sites.
**Reasoning required:** Which calls are guarded against 0-on-unbuilt-history? Which aren't? A single unguarded `iATR` returning 0 that feeds a division will produce Inf/NaN that propagates silently.
**Action:** Every native indicator call must be followed by a validity check. `iATR` returning 0 → abstain. `iRSI` returning 0 on first bars → abstain. No division by an indicator output without a guard. This is a mechanical audit — every call site, no exceptions.

### 7C. Currency strength integration
**Target:** `CalculateCurrencyStrength()`, `GetCurrencyStrengthDivergenceAtBar()`, `GetCurrencyStrengthWeight()`, `DeriveCurrencyStrengthWeights()`.
**Reasoning required:** Is currency strength actually contributing signal, or is it noise? What is its measured IC per regime? If IC is near zero, it's consuming weight budget without contributing.
**Action:** Measure IC per regime. If IC < threshold in a regime, auto-decay its weight toward zero in that regime. Don't remove it — let the evidence decide.

---

## 8. STATE & PERSISTENCE — survive everything

### 8A. Cold start / gap recovery
**Target:** `OnInit`, the state loading path, weekend gap handling.
**Reasoning required:** What happens on the first tick after a weekend gap? After a terminal crash mid-trade? After a broker reconnect with a 2-hour hole in history?
**Action:** Verify: (a) open positions have their stops verified on first tick, (b) state load validates schema version and field count, (c) insufficient history → abstain all layers until history is sufficient, (d) no division by zero on the first bar.

### 8B. Re-entrancy / lock integrity
**Target:** `AcquireLock()` / `ReleaseLock()` (lines ~1270–1271), the OnTick guard.
**Reasoning required:** Can any return path skip `ReleaseLock()`? Can a runtime error (e.g. array out of range) leave the lock held?
**Action:** Guaranteed-release pattern: the lock is released in a finally-equivalent structure (since MQL4 lacks try/finally, use a flag that is checked and released at every return point, or restructure so there is exactly one return point after the lock). Verify by tracing every return path.

---

## 9. FORGE INDICATOR RAMP-UP — accelerate evidence gathering

### 9A. Ghost-based IC seeding for F1–F4
**Target:** The "not yet calibrated (insufficient resolved samples)" path for the forged indicators.
**Reasoning required:** The indicators are wired but contributing nothing because they haven't seen enough outcomes. Ghost/shadow evaluation on historical data could seed their IC without waiting for live trades.
**Action:** Run F1–F4 through the existing ghost evaluation engine on historical bars. Use the ghost results to seed the initial IC estimate (with a discount factor vs live-confirmed IC). This lets the indicators start contributing sooner while their live IC builds up.

---

## 10. SYSTEM UNITY VERIFICATION — the whole, not the parts

### 10A. End-to-end signal trace
**Action:** Trace one complete decision from raw bar data → regime classification → indicator computation → layer votes → trims → unified score → entry gate → sizing → order send → outcome recording → learning update. Every step must use the same scorer, the same regime label, the same bar reference. Any discontinuity is a seam bug.

### 10B. Adversarial input sweep
**Action:** Feed the system: (a) a flat market (ATR → 0), (b) a gap open (price jumps 5%), (c) a spread spike (spread → 10× normal), (d) zero volume bar, (e) history hole (Bars drops by 1000 mid-session). Verify that every case results in a safe, logged, explained outcome — never a blind trade, never an unlogged skip, never a crash.

### 10C. Compile and regress
**Action:** Final build compiles zero errors, zero warnings. Every existing test (T1–T12 from the acceptance matrix) passes. No prior capability regressed.

---

## 11. CONVERGENCE REPORT (mandatory output)

The agent must produce, at the end of the pass:

```
For every region of the codebase:
  - Examined: yes/no
  - Status: sound / weak / overhauled
  - If overhauled:
    - What was wrong (root cause class)
    - Alternatives considered (with trade-offs)
    - Alternative selected (with reasoning)
    - What changed (line regions, function names)
    - Sync verification (which consumers updated)
    - Net effect on system capability
  - If sound:
    - Brief statement of why (one line)

Summary:
  - Regions examined: N
  - Sound as-is: N
  - Overhauled: N
  - Root cause distribution (by class)
  - Residual open items (if any, with honest reason)
  - Compile result: errors / warnings
  - Acceptance matrix: T1–T12 pass/fail
```

---

## 12. DEFINITION OF DONE — the system produces real-world decisions

This pass is done when all of the following are true — not most, all:

**Correctness:**
1. Every function in the codebase has been examined and accounted for in the convergence report.
2. Every weak link identified has been reasoned through with ≥3 alternatives, the best selected with written justification, and the change implemented in sync with all consumers.
3. The dual scorer is eliminated — one scorer, everywhere, calibration through live.
4. The system compiles zero errors, zero warnings.
5. Acceptance tests T1–T12 all pass.

**Dead code resolved:**
6. Every orphaned function is either resurrected and fully wired (with tests) or deleted with all references removed.
7. `g_CalibSilent` is audited and eliminated — logic ungated, logging converted to TLog with level control.
8. No function in the codebase has zero callers. No code path is unreachable.

**Calibration pipeline clean:**
9. The INDINTEL ranking matches the live execution metric (simulated outcome, not raw return).
10. Holdout contamination is proven absent — one global split, assertion-guarded.
11. Sparse regimes have an honest strategy: `UNQUALIFIED` stand-down + evidence-gathering promotion path.
12. Calibration timeout writes are flagged `TRUNCATED` and never consumed as complete.

**Risk & execution hardened:**
13. `CalculateKellyCeiling` is resurrected and wired as the sizing authority, regime-conditioned, ½-Kelly capped.
14. `CanTakeAnotherTrade` is resurrected as a regime-aware hourly frequency gate.
15. Spread/cost calibration seeds at init and hard-blocks until minimum sample gathered.
16. Every order error code has an explicit handler. No position exists without a stop for more than one tick.

**Observability complete:**
17. TLog appends, not overwrites. Rolling rotation at 2MB.
18. Every CPU-bound loop > 1000 iterations has a progress TLog at fixed intervals.
19. Structured decision log is complete per schema (§H of the annex) — every decision replayable offline.
20. `GetRejectReasonText` is resurrected and wired into every rejection log entry.

**Self-regulation proven:**
21. Regime quarantine triggers on drift detection, re-promotion requires full OOS gauntlet.
22. Online weight nudges are bounded per step, clamped to [min,max], with auto-rollback on degradation.
23. End-to-end signal trace (§10A) completed — one decision traced from bar data to outcome, no seams found.
24. Adversarial input sweep (§10B) completed — flat market, gap, spread spike, zero volume, history hole — all safe.

**The bar:**
After this pass, the system is capable of producing real-world trading decisions — entries, exits, sizing, and self-management — on a live demo account without requiring human intervention for correctness. It may still need human oversight for edge validation (L7 of the thesis), but it no longer needs human intervention to *function correctly*. That is the difference between "still building" and "ready to prove itself." This pass crosses that line.

**The measure of this pass is not how many things were changed but how few weak links remain. The ideal outcome is a system where the next agent pass finds almost nothing to fix — because this one was thorough enough to leave almost nothing behind. That is what a hero does: finishes the job so thoroughly that no one needs to come back.**
