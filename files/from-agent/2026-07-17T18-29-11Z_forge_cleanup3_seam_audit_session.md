---
name: forge-cleanup3-seam-audit-session
description: "2026-07-17: forge-cleanup-3 installed and run -- WARRANT#54-59/SLS(68) shipped, found and fixed the same coherence bug (hardcoded 20-bar exit / wrong TP-SL bracket instead of the validated per-regime values) in 6 places across Phase 3B, Ghost Mode, and conviction-tier learning. No live testing performed (explicit user instruction)."
metadata:
  node_type: memory
  type: project
  originSessionId: current
---

Manuel delivered `FORGE-CLEANUP-3_THESIS.md` as a local file on Desktop (not via mailbox) and
asked to install it as an agent and run it repeatedly, unprompted, until the calibration-suite
coherence problems were patched -- with an ambiguous "NO LIVE TESTING" instruction that needed
clarifying (could have read "DO live testing"). Asked via `AskUserQuestion`; Manuel confirmed
**NO live testing**, and added "you can branch off strategies and choose the most successful
hybrids" -- interpreted as: where a seam-fix has multiple reasonable implementations, pick the
best-reasoned one by design criteria, not by empirical backtest (none was run).

**Installed as skill:** `forge-cleanup-3` (`~/.claude/skills/forge-cleanup-3/SKILL.md`), same
provenance-header template as `forge-parallel`. Its thesis: audit every phase-to-phase *handoff*
in the calibration suite (not phase-internal correctness), with the live 14-layer scorer as the
fixed reference the whole chain must agree with. Six named seams (§2 of the thesis): exit horizon
-> Phase 3B, localisation -> weight search, weight search -> TP/SL, TP/SL -> ProbDB, ProbDB
save->load, whole suite -> live engine.

**What the audit actually found (real code, `TUNGSTEN_9.82_A7.5_QUANT_SLS(68).mq4`, 57.5k lines):**
the exact same coherence bug, in six separate places -- a hardcoded 20-bar exit window (and in one
case a third, different hardcoded ATR bracket) instead of the already-validated, per-regime
`g_RegimeOptimalExitBars`/`g_RegimeOptimalSLMult`/`g_RegimeOptimalTPMult` that WARRANT#51/52
(2026-07-17, earlier the same day) had just finished properly validating. Each instance measured
a *different* "win" than the one the search/gate it belonged to was supposed to be judging against
-- textbook handoff/seam failure, not a phase-internal bug (matches the thesis's own framing
exactly). Fixed as **WARRANT#54-59 -> still SLS(68)** (build id unbumped this pass -- compile-only
verification, no new build number assigned; flag for whoever next touches EA_BUILD_ID), each
compiled clean (0 errors, 1 pre-existing unrelated warning) via `metaeditor.exe` after every edit:

- **WARRANT#54** (seam: exit horizon -> Phase 3B) -- `OptimizeComponentWeightsForRegime`'s own
  holdout fit-check and its FIX(30) enhanced-scorer cross-check both hardcoded `-20`, while the
  function's own training objective (`barOutcomes`, same function) correctly used the validated
  `exitHorizon`. Phase 3B was training on one definition and validating itself on another.
- **WARRANT#55** (seam: localisation -> weight search) -- Stage -1 (`MeasureComponentSensitivity`,
  the component-isolation scan that decides which components get the grid search's full attention)
  and its isolation-seed evaluation both hardcoded `-20` too. The localisation step that steers
  Phase 3B's search was scored under a different function than the search itself.
  Also audited the mirror-regime IC pooling (SLS28-CLAUDE, Strong Bull<->Strong Bear evidence
  pooling) as a *candidate* coherence break -- concluded it's legitimate, well-justified
  statistical shrinkage (only pools when divergence is indistinguishable from sampling noise,
  documented with a real empirical counter-example), not a re-smearing artifact. No fix needed;
  logged as audited-and-clean, per the thesis's own framing that a seam can pass.
- **WARRANT#56** (seam: weight search -> TP/SL) -- Phase 3B's *base* per-regime weights are always
  fit under a fixed 1.5/2.5 ATR bracket (3B runs before Phase 3C picks the real per-regime
  bracket); only 3B.5/3B.6 (session/vol refinement) used the real bracket, and only when they had
  >=500 bars to validate on. Added `ValidateWeightsAgainstFinalBrackets()`, called once right
  after Phase 3C, before 3B.5/3B.6 -- a cheap re-validation pass (not a full re-optimization) that
  re-measures each validated regime's WR under its real final bracket and either regularizes
  toward equal weights (same 35%-blend convention used elsewhere) or replaces the recorded WR with
  the honest final-bracket number. Same shape as the existing FIX(30) cross-check, reused against
  the bracket seam instead of the linear/enhanced-scorer seam.
- **WARRANT#57** (seam: ProbDB save -> load) -- the real, previously-known gap (flagged in the
  codebase's own WARRANT#43 comment: "no dedicated Save/LoadProbDB found", also in
  [[forge4d_pass11_dense_session]]'s "ProbDB confirmed to have zero persistence"). Built full
  versioned persistence: `PDB_WriteArmedTail`/`PDB_ReadArmedTail`, same guarded-tail-marker
  precedent as `LE_WriteArmedTail`/`LE_ReadArmedTail` (WARRANT#32), living in `SaveSystemState`/
  `LoadSystemState` only. Schema-versioned (mismatched version -> skip and rebuild fresh, never
  misread). E5's "decay" requirement implemented as: confidence exponential half-life (14 days,
  floored at 0.15, never fully erased) applied at load time only -- wins/losses/winProbability
  themselves are untouched, only how much the live system trusts them decays. A restore older than
  60 days is treated as too stale to trust at all and left uncalibrated (forces a fresh Phase 4
  build) rather than silently trading a possibly-stale regime read.
- **Seam "TP/SL -> ProbDB" audited, found already coherent** -- `BuildProbabilityDatabase` (Phase
  4) already uses `CalculateEnhancedUnifiedScore` (real live scorer) and the real per-regime
  `g_RegimeOptimalExitBars`/`SLMult`/`TPMult` for outcome labeling, and `QueryProbabilityDatabase`
  matches on the same regime/score/ATR/hour frame patterns were built with. No fix needed.
- **WARRANT#58** (seam: whole suite -> live engine) -- `RunGhostMode` (Phase 5, literally the
  "does the final config agree with what live will do" check) already used the real live scorer
  and Phase 3C's real brackets, but still hardcoded a 20-bar exit walk-forward. A ghost "pass"
  measured under the wrong horizon wasn't evidence the live config would do what Ghost said.
- **WARRANT#59** (same seam) -- `LearnConvictionTiers` (derives `g_TierGood`/`g_TierExcellent`,
  live-used conviction-tier boundaries) hardcoded a *third*, different bracket (2.0/1.3 ATR, 20
  bars) distinct from both Phase 3B's 1.5/2.5 and the real per-regime one. Fixed to use the real
  per-regime bracket, confirmed it runs after Phase 3C in the call order.

**Round 2 (same session, deeper methodology on Manuel's request -- "no dumb logic tests, hyper
intelligent methodology"):** instead of re-grepping the same hardcoded-20 pattern, audited for
threshold-SPACE and scorer-IDENTITY mismatches -- a fundamentally different, harder-to-spot bug
class. Traced all three coexisting threshold conventions in this codebase (raw CEUS signed
magnitude 0..100 vs neutral=0; `g_RegimeOptimalThresholds`/`g_CurrentThreshold` signed-margin
16..90, needing the documented `50+thr/2` bridge; `engine.unifiedScore`/`buyThresh`/`sellThresh`
normalized 0..100, 50=neutral) and checked every comparison for the right bridge.

- **WARRANT#60** (seam: whole suite -> live engine) -- found `CreateCircuitBreakerGhost()`
  (decides whether circuit-breaker recovery ghost trades "pass," gating whether real trading
  resumes after a drawdown halt) explicitly commented "same gate as live trading" but wasn't, two
  compounding ways: (1) called the LEGACY `CalculateUnifiedScoreFromComponents()` instead of CEUS
  (`CalculateEnhancedUnifiedScore`), and (2) compared that raw 0-100 score directly against
  `g_CurrentThreshold` with no `50+thr/2` bridge applied -- e.g. a threshold of 70 (meant to gate
  at normalized 85) was actually gating at 70, letting materially weaker signals through than real
  live trading would ever accept. Also discovered `engine.unifiedScore` goes stale during circuit-
  breaker ghost mode (the main per-tick CEUS refresh in `OnTick` is behind an early-return that
  `ProcessGhostMode` trips before reaching it), so the fix computes a fresh bridged CEUS read
  in-function rather than trusting `engine.unifiedScore`. This means the safety mechanism meant to
  prove the system is ready before resuming real trading was, before this fix, an easier bar to
  clear than real trading itself -- exactly backwards for a recovery gate.
- Checked `ProcessDiscoveryMode`/`CreateGhostTrade` (the OTHER early-return-guarded mode) for the
  same pattern -- concluded it's architecturally different and NOT a seam bug: Discovery Mode is
  an explicit parameter-sweep search (its own `testScore`/`testThreshold` are both self-consistent
  0-100-space values it defines and compares internally), not a claim to reproduce the live gate,
  so there's no "same gate" promise being broken. Left untouched.

**Not done, deliberately:** no MetaTrader/Strategy Tester run of any kind (explicit instruction).
No forge_ledger.json update -- searched Desktop/Work and `.relay-mailbox` for it, not found on
disk in this environment; did not fabricate one without knowing its real schema/history. EA_BUILD_ID
string was not bumped past SLS(68) -- these are source-level fixes verified by compile only, not a
new numbered build; whoever attaches this to MT4 next should treat it as SLS(68)-plus-WARRANT#54-59,
not assume the build banner reflects it.

**How to apply:** per the thesis's own §5/§6 honesty floor, this pass proves the calibration suite
is *internally coherent* (every seam now measures "win" the same way the stage it feeds does) --
it does NOT prove a live edge exists or that these fixes change live P&L in any particular
direction. That verdict only exists after a real, consented calibration run, which was explicitly
out of scope this pass. Next step is Manuel's call: attach and run (manually via GUI per
[[mt4_ea_swap_automation]]'s standing recommendation), or continue auditing for more instances of
the same bug class before running. A `grep -n "bar-20)\|bar - 20)"` sweep across the file found
three more hardcoded-20 hits beyond the six fixed above; all three were triaged and judged
intentional/non-seam (a PASS13 feature diagnostic and Phase 1's baseline threshold measurement,
both deliberately regime-agnostic by design, need a constant yardstick rather than a per-regime
one) -- but this was a targeted grep, not an exhaustive sweep of every TP/SL walk-forward loop in
the file, so more instances may exist unfound.
