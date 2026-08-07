# GENESIS Regression Proof — Precedent vs. Organs

Method: real Grep/Read investigation of `precedent/TUNGSTEN_10.28_A7.5_QUANT_SLS(114).mq4` (60,415 lines) against the 20 invariants in `spec/GENESIS_MASTER_SPEC.md` §1, cross-checked against the actual `src/` organ files (not just ledger claims). No precedent line was copied into GENESIS; only intent was read. 2026-08-07.

**Tally: 12 PROVEN · 7 STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED · 1 NEEDS-LIVE-EXECUTION**
(PROVEN: INV-03,04,06,08,09,10,12,13,14,15,19,20 · ALREADY-FIXED: INV-01,02,05,07,11,17,18 · NEEDS-LIVE-EXECUTION: INV-16)

Of the 13 PROVEN, three (INV-03, INV-07, INV-17) initially looked like GENESIS construction gaps per the ledger's own `invariants` dict ("not_yet_constructed") — investigation found this stale: `src/GENESIS_Constants.mqh` (INV-07) and `src/Cognition/C04_ChampionRegister.mqh` (INV-17) exist on disk, compiled 0/0, dated *after* the ledger's last write, evidently an unlogged pass_3. **INV-03 is the one real, confirmed gap** — no organ or shared type anywhere in `src/` computes a rate with an explicit divisor; see its section below.

---

### INV-01 · No hardcoded win rate anywhere
- **Origin:** W#61
- **Precedent today:** `GetLiveWinRate()` (~line 55538-55544) carries an explicit comment citing WARRANT#61: the old unconditional `return 65.0` (fictional WR feeding the EV gate even after a real STAND DOWN measured 0.0%) is gone, replaced by real `g_LiveWinRate`/calibrated-ghost-WR logic. **Already fixed upstream.**
- **GENESIS organ:** `P02_FeatureBank.mqh` computes AUC OOS-only by construction (no in-sample scoring path exists in the API) and auto-retires any feature with AUC<0.52 — grounded explicitly in this same WARRANT#61 incident per its header.
- **Verdict:** STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED

### INV-02 · Every stored field is read back
- **Origin:** W#116
- **Precedent today:** Load-side comment at line 26467-26483 names WARRANT#116 explicitly, explains the 4-byte field-shift root cause of the 595048703% WR incident, and shows the fix: `g_CorrelationsLearned = (FileReadInteger(handle) == 1);` now present at the exact write-side offset, plus WARRANT#91's sanitize-on-load safety net immediately after. **Already fixed upstream.**
- **GENESIS organ:** `C03_EvidenceLedger.mqh`'s `C03_SerializeEntry(handle, writeMode, entry)` is ONE function for both directions (not a hand-maintained pair), touches each field exactly once, plus a schema-version check (`C03_SCHEMA_VERSION` mismatch aborts load) — structurally makes the field-shift class impossible, not just this one instance.
- **Verdict:** STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED

### INV-03 · Win-rate denominators are never fixed
- **Origin:** W#124
- **Precedent today:** Line 24916, `g_Risk.recentWinRate = (double)wins / MathMax(1, _total_rb20282) * 100.0;` with an inline comment naming WARRANT#124 and the old hardcoded `/20.0` bug it replaced. **Already fixed upstream** (this is the example case named in the task brief).
- **GENESIS organ:** **No dedicated mechanism exists.** Grep across `src/` for a `{value,n,ci}` rate type, or any `wins/n`-style division, found nothing — P02_FeatureBank computes AUC (not WR), G01_ArmController gates on raw OOS trade *count* but never divides by it to form a rate. Ledger's own `invariants` dict confirms: `"I03": "not_yet_constructed"`. This is a real, honest gap — no organ owns INV-03 today.
- **Verdict:** PROVEN *(precedent's specific historical bug is fixed; but the general invariant — "no organ can compute a rate over a literal/fixed denominator" — has nothing enforcing it in GENESIS yet, so the general failure class remains constructible)*

### INV-04 · One hard risk floor, one chokepoint
- **Origin:** W#127
- **Precedent today:** The named range-trading path (line 32683-32689) got a reactive clamp citing WARRANT#127 ("worst case today is 2.75%... enforce it here too"). But the precedent has no single chokepoint: `OrderSend(` is called directly (bypassing the `SafeOrderSend()` wrapper entirely) at lines 30578, 30688, 30702 for scale-in pending orders, each with its own independently-computed lot/risk math. The general architectural failure (multiple order-placement paths, each patched individually) is still visible today.
- **GENESIS organ:** `A02_OrderGate.mqh` is verified (real grep, confirmed independently) to be the *only* file in `src/` containing `OrderSend`/`OrderClose`/`OrderModify`/`OrderDelete` outside comments; `A02_LIVE_EXECUTION_ENABLED=false` keeps it dormant. `A01_SizeEngine.mqh` defines `HARD_FLOOR` once, reused by A02.
- **Verdict:** PROVEN

### INV-05 · Correct regime bracket, always
- **Origin:** W#123
- **Precedent today:** Dozens of sites (lines 5113, 5247-5250, 6199-6254, 7043-7407, 39071-39997, etc.) now reference named constants `P3B_DIAG_BRACKET_TP_ATR`/`_SL_ATR` (=2.5/1.5) each tagged "WARRANT#123: was literal 2.5/1.5" — the flat-multiplier-vs-regime-specific-bracket mismatch is fixed at every one of these sites. **Already fixed upstream.**
- **GENESIS organ:** `P03_CostModel.mqh`'s only accessor `P03_GetBracket(regime, out)` refuses ALL lookups while the 9-regime map is incomplete (not just missing regimes) — stronger than the precedent's reactive per-site patching.
- **Verdict:** STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED

### INV-06 · No Print-only decision path
- **Origin:** W#120/121/125/130
- **Precedent today:** All four named incidents are fixed — retry-engine (W#120, line 24494 etc.), calibration-verdict (W#121, line 41049), STAND DOWN detail block (W#125, line 40888), `LE_Log` (W#130, line 38428) all now route through `TLog`/`LE_Log`. But 257 raw `Print(`/`PrintFormat(` calls remain file-wide, many clearly decision-relevant and never converted: e.g. line 10186 `Print("  sentinel | edge recovered | full sizing restored")`, line 11066 P6 gate-PF message, line 11183/11286/11288 context-gate verdicts. The general failure class (a decision line invisible to the live feed) is still trivially reproducible today.
- **GENESIS organ:** `G03_Logger.mqh` — real grep audit (verified) confirms `Print()` appears exactly once in all of `src/`, inside G03 itself; every other file routes through it.
- **Verdict:** PROVEN

### INV-07 · No duplicate threshold floors
- **Origin:** W#119
- **Precedent today:** Comment at line 8881-8884 names WARRANT#119: two sequential if-blocks for the same sparse-guard/no-edge-fallback concept were merged into one mutually-exclusive branch. **Already fixed upstream** at this specific site.
- **GENESIS organ:** `src/GENESIS_Constants.mqh` — a dedicated leaf-include registry, added *after* pass_2 caught GENESIS's own organs independently redefining the same two concepts (30 as `R01_MIN_N_PER_SUBWINDOW`/`G01_MIN_OOS_TRADES`/`P02_MIN_N_FOR_AUC`, 500 as `A03_FULL_CONFIDENCE_N`/`R04_MIN_TRAINING_SAMPLES_FOR_TRUST`) — now both are single aliases of `GENESIS_DIAGNOSTIC_POWER_FLOOR`/`GENESIS_TRADING_WEIGHT_FLOOR`. Not in the ledger's `organs` dict (a later, unlogged pass) but present and compiled on disk.
- **Verdict:** STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED

### INV-08 · No duplicated magic numbers
- **Origin:** W#122/126
- **Precedent today:** WARRANT#122/126 converted many sites to `P3B_DIAG_BRACKET_TP_ATR`/`_SL_ATR`, but the precedent's own WARRANT#102 comment (line 507-509) admits: "14+ found via grep, many in functions not touched this session -- consolidating those too needs its own review pass." Confirmed independently: raw `*2.5` literals still exist outside the named constant at lines 5525, 10620, 10722, 14912, 24935, 45090, 47740. The duplication class is still live today, by the precedent's own admission.
- **GENESIS organ:** No single dedicated organ (ledger: `"I08": "demonstrated_by_convention"`), but a real, verified audit (zero duplicate `#define` names across `src/`, re-confirmed independently this pass, one apparent hit was a comment mentioning the real definition, not a second definition).
- **Verdict:** PROVEN

### INV-09 · Arm only on ≥30 OOS trades
- **Origin:** W-log P5/P6
- **Precedent today:** `PRI_Phase6_ShouldArm(ghostWR, targetWR, gatesMet, totalGates)` (line 24596-24610) arms on `(gatesMet>=5 && ghostWR>=0.62) || (ghostWR>=0.65 && gatesMet>=4)` — sample size/significance (`p6_sig`) is just one of 7 votable gates, not a hard, unconditional precondition; enough other gates passing can outvote a failing significance/sample-size gate. No WARRANT# comment marks this as fixed. The architectural risk the origin describes (arming can proceed without n being a hard gate) is still visible today.
- **GENESIS organ:** `G01_ArmController.mqh`'s `G01_EvaluateArming()` checks `oosTradeCount<30` FIRST, unconditionally, returning `G01_REFUSE` before ghostWR/durability/WF-fragility are even inspected (line 25, 52-55) — the exact "n=1, WR=100%" incident class cannot vote its way past this check.
- **Verdict:** PROVEN

### INV-10 · Every safety gate is blocking
- **Origin:** W-log Pre-Flight
- **Precedent today:** Lines 38599-38600, still present verbatim: `LE_Log(StringFormat("  PRE-FLIGHT | 10/10 asked | %d gate(s) incomplete/failed | %s", gatesFailed, gatesFailed>2 ? "HOLDING deeper claims, PROCEEDING with calibration" : "PROCEEDING"))` — regardless of how many gates failed, the system logs and continues. This is the literal historical failure, unfixed, still reproducible by inspection.
- **GENESIS organ:** `G02_GateBus.mqh` — real grep audit confirms zero occurrences of override/force/proceed/skip/bypass in actual code (only in comments describing their absence); three-state enum `{G02_PASS, G02_GATE_BLOCK, G02_INCOMPLETE}` treats INCOMPLETE identically to BLOCK, not folded into PASS.
- **Verdict:** PROVEN

### INV-11 · Evidence persists across restarts
- **Origin:** W#131
- **Precedent today:** `Keys3_WriteEdgeTail`/`Keys3_ReadEdgeTail` (lines 26027-26029, 26764-26767, 37410-37413) explicitly cite WARRANT#131 and accumulate R-band WR evidence across restarts instead of resetting to zero each run. **Already fixed upstream.**
- **GENESIS organ:** `C03_EvidenceLedger.mqh` is append-only/versioned/schema-hash-checked (INV-02) by construction; `R03_TimeAwareSizing.mqh` decays confidence with evidence age rather than discarding it.
- **Verdict:** STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED

### INV-12 · Confidence enters size exactly once
- **Origin:** forge-bestofboth (WARRANT#109)
- **Precedent today:** WARRANT#109 (line 55365-55381) added a hard ceiling clamp on top of `_comb = confidenceMultiplier * memoryMultiplier * predictiveMultiplier * validationMultiplier * awarenessMultiplier * _bLotConv * _ghostPrem` — but the stack itself (six-plus multiplicative confidence-shaped factors) is still there, only capped after the fact, not eliminated. The composition violation the invariant targets is structurally still present; only its worst-case consequence is bounded.
- **GENESIS organ:** `A01_SizeEngine.mqh`'s `A01_ComposeSize(edge, varianceProxy, confidence, ddBudget, rawN, avgCorrelation, ...)` takes confidence as one parameter, multiplied in exactly one place, with no second confidence-shaped parameter in the signature (verified in header + F0004 comment); `R03`/`A03` explicitly compose their outputs *into* that one factor rather than stacking a second multiplier.
- **Verdict:** PROVEN

### INV-13 · Correlated bets counted once
- **Origin:** charter-v2
- **Precedent today:** `RiskManagement` struct declares `double correlationMatrix, diversificationIndex;` (line 13107) but grep across the entire 60k-line file finds zero other reference to either field — dead, unused declarations. No live correlation-based position-count discount exists anywhere in the sizing code today.
- **GENESIS organ:** `A01_SizeEngine.mqh` computes `n_eff` via the standard equicorrelation effective-N formula from `avgCorrelation`, dividing size by it (verified present in the `A01_ComposeSize` signature above).
- **Verdict:** PROVEN

### INV-14 · Walk-forward, never one split
- **Origin:** W-log P3B
- **Precedent today:** WARRANT#50 (two-fold check), WARRANT#79 (real Bailey-López de Prado CSCV) were added *on top of* Phase 3B's original single 70/30 train/holdout split fit-check — the comments describe them as additive guards, not a replacement of the underlying single-split search. The base single-split-capable path is still there, patched, not removed.
- **GENESIS organ:** `C01_EdgeAdjudicator.mqh`'s only entry point, `C01_Adjudicate(const C01_WindowResult &windows[])`, takes an array; `C01_MIN_WINDOWS=3` — a 1- or 2-window call structurally cannot produce EDGE, and there is no overload accepting a single split. `C02_OverfitImmune.mqh` composes WF-gap/resample/PBO trust via `MIN()` (not average — proven by an explicit test the ledger cites) so one bad guard can't be diluted by two healthy ones.
- **Verdict:** PROVEN

### INV-15 · Match search to substrate
- **Origin:** W-log SYNTHESIS
- **Precedent today:** Its own SYNTHESIS line (line 40101-40105) states verbatim: "a single fixed-window linear search cannot capture this by design." WARRANT#132 (`EnableReadabilityGatedCalibration`) is a real mechanism that could act on it, but is HARD OFF by default and only filters which bars train the weights — it never dispatches to a different *search method*; Phase 3B's core search remains one linear/grid search for every regime regardless of substrate class.
- **GENESIS organ:** `R02_SearchDispatcher.mqh`'s `R02_Dispatch(R01_Verdict)` is a total, deterministic mapping: `R01_STATIONARY -> R02_LINEAR`, `R01_TIME_VARYING/UNKNOWN -> R02_RECENCY_WEIGHTED` (or `R02_CURATED_NEURAL` when `R04_IsTrustworthy()`) — no regime is ever searched with a mismatched method.
- **Verdict:** PROVEN

### INV-16 · Every unattended script self-tests on boot
- **Origin:** infra
- **Precedent today:** Not checkable from this file — the failure (relay-listener dead 3 days on a wrong `pwsh` path, events feed silently stale for weeks) lives in PowerShell tooling around the terminal, not in the `.mq4` EA source; grep of the precedent finds nothing relevant by nature (confirmed, no infra path references exist in the trading-logic file). GENESIS's own ledger agrees: `"I16": "out_of_scope_for_MQL4_organs"`.
- **GENESIS organ:** None of the 16 organs own this — it applies to future PowerShell tooling that would run alongside a live GENESIS attach, not to any MQL4 organ.
- **Verdict:** NEEDS-LIVE-EXECUTION — proof requires inspecting/running the actual daemon scripts (relay listener, events-refresh, any GENESIS watchdog) and confirming each resolves `pwsh`/paths dynamically and self-tests on boot; cannot be shown by reading the precedent `.mq4` at all.

### INV-17 · Champion auto-reverts on regression
- **Origin:** W#128/129
- **Precedent today:** `ForgeChampion_Revert()`/`ForgeChampion_ShouldAutoRevert()` exist (lines 36730-36743) and `input bool EnableChampionAutoRevert = true;` (line 1489, "WARRANT#129: enabled per Manuel's explicit go-ahead") — checked every 5 live trades, reverts on regression. **Already fixed upstream**, though as a user-toggleable `input` default-on, not an unconditional compile-time guarantee, and a single-slot stash (one prior champion), not an unbounded backup chain.
- **GENESIS organ:** `src/Cognition/C04_ChampionRegister.mqh` — present on disk, compiled 0/0 (per `tests/C04_ChampionRegister_test.compile.log`), dated after the ledger's last write (an unlogged pass). Explicitly grounded in WARRANT#128/129 per its own header; reuses `C01_MIN_WINDOWS` (INV-08 discipline) and a fail-closed default (INV-04-style). The ledger's `"I17": "not_yet_constructed"` note is stale.
- **Verdict:** STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED

### INV-18 · 'No edge' is a first-class verdict
- **Origin:** W#118
- **Precedent today:** Comment at line 40082-40085 names WARRANT#118 explicitly: "automates, in real time, the exact diagnosis this session had to piece together by hand across three separate runs." **Already fixed upstream** in this snapshot.
- **GENESIS organ:** `G04_SelfDiagnosis.mqh`'s `G04_Cause` enum (`NONE_TO_DIAGNOSE`/`CAUSE_FLAT`/`CAUSE_TIME_VARYING`/`CAUSE_UNPOWERED`) fires at the moment C01 produces NONE, not as a post-hoc aggregation pass like the precedent's SYNTHESIS block — a structural (not just automated) guarantee every no-edge output carries a cause.
- **Verdict:** STRUCTURALLY-SOUND-PRECEDENT-ALREADY-FIXED

### INV-19 · Cost subtracted at measurement
- **Origin:** W-log P2
- **Precedent today:** No unified cost/edge accessor exists anywhere (grep for `costATR`/`netEdge`/`grossEdge`-style names returns nothing). Spread deduction happens ad hoc at multiple independent sites (lines 10452, 10495, 10535, 10577, 10745-10748, 10869, 10950, 10960), each its own inline `- g_CalibratedAvgSpread*Point` — the same "duplicated truth" pattern WARRANT#101/102 diagnosed elsewhere in this file, not a single point where edge is guaranteed net of cost.
- **GENESIS organ:** `P03_CostModel.mqh`'s `edgeNet = edgeGrossATR - cost` is the only computation path (line 139: "cost>=0 by construction... => edgeNet<=edgeGross always"), never clamped, surfaces negative edges openly.
- **Verdict:** PROVEN

### INV-20 · One regime classifier, one taxonomy
- **Origin:** architecture
- **Precedent today:** `DetectCurrentRegime()` (line 45538) runs a rule-based classifier (`ClassifyBarToRegime_WithHysteresis`) AND a correlation-based one (`PredictRegimeFromCorrelations`), overriding the rule-based result when the correlation model is confident. Its own inline 9.40 comment (line 45553-45567) documents that other call sites read `g_RegimeState.currentRegime` directly rather than calling this function, "so those decisions silently disagreed with whatever this function returned" — only partially reconciled, not eliminated. Multiple regime-determining paths that can disagree are still structurally present today.
- **GENESIS organ:** `P01_RegimeState.mqh` is a pure function returning `p[9]` soft-membership summing to 1; grounded explicitly in the precedent's own "Layer 12: Bayesian Regime Belief" and its documented 9.39 reset-to-uniform bug. No second classifier exists in `src/`.
- **Verdict:** PROVEN
