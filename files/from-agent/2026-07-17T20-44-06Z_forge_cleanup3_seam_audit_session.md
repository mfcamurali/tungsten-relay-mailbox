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

**PAUSED mid-task 2026-07-17 (wifi slow, resume later):** after WARRANT#60 and the mailbox send
(source .mq4/.ex4, forge-cleanup-3 SKILL.md, and this memory file all pushed to
`tungsten-relay-mailbox` as file attachments, plus a summary message -- all confirmed pushed,
`PUSH_EXIT=0` both times), Manuel asked to run **two full tungsten-smithing passes** across
forge-indicate/forge-edge-2/forge-4d-alpha/forge-parallel, informed by the WARRANT#54-60 fixes.
Loaded the `tungsten-smithing` skill and confirmed the REAL current state directly from source
(don't trust the skill file's own stale "WARRANT#40" claim):

- **Latest build: SLS(68)**, latest warrant shipped: **WARRANT#60** (this session's own
  forge-cleanup-3 work) -- so the next smithing warrant is **WARRANT#61**.
- **forge-indicate**: last real r-stage shipped = WARRANT#47 (r6, offline indicator fine-tuning
  acceptance rule). r1-r6 done (partial on r4/r5 per their own comments: WARRANT#40 "3G ... dynamic
  range only", WARRANT#42 "3H ... hysteresis only"). **Next: r7** (Σ convergence + gates:
  reliability, relationship-OOS, threshold-target, per-regime ghost power) or complete the r4/r5
  partials (perfect-buy/sell envelope; conviction-grading) -- read fully at
  `~/.claude/skills/forge-indicate/SKILL.md`, already loaded this session.
- **forge-edge-2**: r1 (WARRANT#33), r5 ProbDB annotation (WARRANT#43), r6 partial -- Bayesian
  live-cell core + capped-Kelly stack (WARRANT#44) shipped. **Not yet confirmed shipped: r2 (Phase
  3D dwell & bracket, `0xE512`), r3 (Phase 3C cell-informed TP/SL), r4 (Phase 3E driver
  fingerprint, `0xE513`)** -- need to grep source for `0xE512`/`0xE513` markers to confirm before
  assuming these are missing (WARRANT#33 thesis says "r1-r7" was its payload, so some may already
  be in under WARRANT#33's own number rather than a separate later warrant -- check before
  building, don't duplicate). Full doctrine already loaded this session at
  `~/.claude/skills/forge-edge-2/SKILL.md`.
- **forge-4d-alpha**: the hardening gate, "always active," not a separate numbered pass -- verify
  it's actually being invoked/checked for whatever gets built next, don't skip it.
- **forge-parallel**: WARRANT#41 (Wave 0 substrate), #45 (Wave 1), #46 (Wave 2) shipped. Wave 3
  (driver-attribution live influence) explicitly gated until Wave 1 OOS-stable + Wave 2 proven --
  neither achievable without a live run, so Wave 3 is NOT the next step; check for remaining
  Wave 0/1/2 sub-pieces first, or move to forge-4d-alpha/forge-indicate/forge-edge-2 work instead.
- **Not yet read this pass**: `forge-4d-alpha` and `forge-parallel` SKILL.md files themselves (only
  forge-indicate and forge-edge-2 were read before the pause) -- read those first on resume.

**Explicit standing constraint for this smithing work (still in force, not renegotiated):** NO
live MetaTrader/Strategy Tester execution -- compile-verify only via `metaeditor.exe` (PowerShell),
same as every WARRANT this whole session. The "real floor reached" note in `tungsten-smithing`'s
own SKILL.md is honest doctrine, not an excuse: S1-S5/PBO gates, the live Bayesian core's actual
promotion decision, Σ convergence's validation, and any ratchet promotion all require a completed,
powered run to mean anything -- keep building genuinely useful GATED-OFF scaffolding (matching the
WARRANT#40/42/44/47 "partial, scoped" pattern), don't claim a gate pass or promotion without one.

**How to resume:** re-read this block, grep the current SLS(68) source for `0xE512`/`0xE513` to
settle forge-edge-2's real r2-r4 status, read forge-4d-alpha + forge-parallel SKILL.md, then pick
one concrete next r-stage per agent for pass 1 (WARRANT#61+), implement, compile-verify, checkpoint,
repeat for pass 2. Send results to the relay mailbox per the same file-attachment pattern used for
WARRANT#54-60 (source, ex4, updated memory).

**LIVE TEST STARTED 2026-07-17 ~18:43, explicit live-user authorization ("test our last complete
version on mt4 and watch logs directly every minute... to see how the fixes are going and what's
still broken methodology-wise or goal-reaching-wise"):** this explicitly supersedes the earlier
"NO LIVE TESTING" scope for forge-cleanup-3 -- that constraint was for the seam-audit/smithing
code work, not a permanent rule; a direct live-chat instruction naming MT4 is exactly the per-run
consent every forge-family thesis requires. Copied the WARRANT#54-60 build (source verified 0
errors, 1 pre-existing warning) into the terminal's actual `MQL4\Experts` folder (the ELITE FIXES
working copy is NOT where the terminal reads from -- confirmed the folder already had a STALE
pre-fix SLS(68) from earlier that day, now overwritten). Swapped `chart02.chr` (USDJPY M5,
window_num 4->5) per the standing [[mt4_ea_swap_automation]] procedure -- used PowerShell
Get-Content/Set-Content array-index edit since `sed -i` failed on permission (temp file in
C:\Windows\System32, not writable) -- confirmed clean via line-count match against the backup
(`chart02.chr.bak_before_sls68_warrant60`). Launched `terminal.exe`, confirmed via the terminal
log within seconds: `Expert TUNGSTEN_9.82_A7.5_QUANT_SLS(68) USDJPY,M5: loaded successfully`.

Armed a persistent `Monitor` (script at
`...\scratchpad\watch_tungsten.ps1`, 5s poll / 60s heartbeat) that: (1) alerts immediately if
`terminal.exe` disappears (the pass-17 silent-hang failure mode) and pulls Application-log Event
1000/1002 if so: (2) emits whenever `TUNGSTEN_live.log` changes (the EA's own overwritten-per-update
progress file, read via `FileShare.ReadWrite` per the standing encoding/locking lesson); (3) emits
new lines appended to the day's terminal log (1252-encoded, same shared-read technique); (4) a
plain heartbeat every 60s regardless, satisfying the "watch every minute" ask even through quiet
stretches. Per [[mt4_ea_swap_automation]]'s own caution, the file-edit swap method has an
unresolved history of sometimes stalling post-init (last confirmed NOT reproducing as of pass 15,
2026-07-14) -- watch for that specifically, don't assume it's fixed.

**What to actually look for once data comes in:** whether Phase 3A/3B now report the SAME exit
horizon consistently in every log line that touches it (WARRANT#54/55/58/59's fix), whether ProbDB
persistence produces a `[LOADED] ProbDB restored` line on any restart during this run
(WARRANT#57), and whether the circuit-breaker ghost gate (WARRANT#60) is exercised at all this run
(only fires if a circuit breaker actually trips) -- absence of that last one is not a failure, just
means the condition never arose.

**Round 3 (same session, 2026-07-17, after the failed live-test attempt): systematic sweep, two
bug classes, both closed clean.** No new WARRANT shipped this round -- a clean audit is itself the
honest result, not a reason to manufacture a fix.

1. **Threshold-space mismatches** (WARRANT#60's defect class): checked every comparison site of
   `g_CurrentThreshold`/`g_RegimeOptimalThresholds` against a score across the whole file (~90
   grep hits triaged). Found none unfixed -- WARRANT#60 (`CreateCircuitBreakerGhost`) was the only
   instance. Everything else is either self-consistently signed-margin (Phase 3B, Ghost Mode
   calibration, `ValidateWeightsAgainstFinalBrackets`, `LearnConvictionTiers`) or correctly bridged
   (`50.0 + thr/2.0`) before comparison against a 0-100-space score (the legacy live-signal
   fallback path, `SyncEngineThresholdsFromCurrent`).
2. **Weight-array ordering**: checked all 17 sites across the file that build a 6-element weight
   array from a `ComponentWeights` struct, and the function that consumes those arrays
   (`CalculateUnifiedScoreCoreAtBar`, L42991). Every site uses
   `[mtf, momentum, volume, volatility, session, pattern]` consistently; the consumer installs them
   into `g_RegimeOptimalWeights` in the same order before scoring through the real
   `CalculateEnhancedUnifiedScore` and restoring the originals -- a genuinely well-engineered
   pattern (temporarily install -> score through the real engine -> restore), not a transposition
   risk. Clean.

**Known, already-self-flagged gap (not a new finding, not fixed this round):** Stage -1
localisation (`MeasureComponentSensitivity`) and `CalculateScoreWithWeights` use a simplified
proxy scorer (raw MTF/MACD/etc. recomputed inline), not the true CEUS 14-layer engine -- the
codebase's own comment (`SLS19-TODO CRITICAL1`, near L7152) already documents this exact gap and
names the real fix (pre-extract CEUS's actual per-bar component decomposition once, reuse
everywhere). Impact is bounded: Stage -1's proxy-scored candidate is only accepted as `bestWeights`
if it beats the real, precomputed-sc0-sc5 composite score afterward (confirmed by reading the
acceptance gate), so a bad proxy search can waste search effort but can't silently ship a worse
result unvalidated. Left as a flagged future item -- fixing it properly means touching CEUS's
internals to expose its decomposition, a bigger and more invasive change than fits a quick patch,
consistent with this session's own pattern of not rushing architecture changes in under time
pressure.

**Live run result, 2026-07-17 20:35 (71 min, USDJPY M5): STAND DOWN, correctly.** Full run completed
end-to-end (all 9 regimes, ProbDB build, Phase 6 ghost, ARMED-state save) and refused to trade:
OOS WR 0.0% vs train 33.6% (-33.6pp drift), 3/6 gates (really ~1 honest pass -- PF 2.00/MaxConsec 0/
p=0.0005 are all n=1 sample artifacts, not real passes), walk-forward fragile. TUNGSTEN's own
diagnosis: "signal patterns are time-specific, not structural." Only 1/9 regimes (Bullish Reversal)
cleared the real >=500-real-bar validation floor; three independent retries of r1 Strong Bull each
produced promising mid-search train/val agreement (up to 68.5/66.7%) and were still rejected by the
deeper floor gates every time -- consistent rejection across independent retries, not a fluke.
**Confirmed live for the first time: WARRANT#56 (`ValidateWeightsAgainstFinalBrackets`) actually
fired and caught a real case** -- r2 Strong Bear scored 38.0% under the training bracket vs 20.0%
under the real final bracket, correctly regularized. Direct proof the seam-coherence work fixes
real, not theoretical, problems. Hang-fix (Sleep(1) in the 50k-draw search) held clean through the
danger point at least 7 separate times across this run. ProbDB persistence (WARRANT#57) produced
its first-ever real save (243,852-byte ARMED file with a ProbDB tail).

**WARRANT#62 -- wait, corrected: WARRANT#61 -- `CalculateRecentWinRate()` hardcoded-65%-fallback
bug, found by reading the run's own output.** The GROWTH projection line printed "$833.05 ->
$60,907,358,767,382.73 ... WR 65.0%" one line above a milestone line correctly showing "WR 0% (-32pp
vs cal)" -- same run, same moment, two irreconcilable numbers. Root cause: `CalculateRecentWinRate()`
(L52958) returned a hardcoded `65.0` whenever `g_WeightsOptimized` was true and no live trades
existed yet, ignoring `g_E99_Validation.expectedWinRate` (the real calibrated/Phase-6 expectation,
32.0% this run) entirely -- and per the function's own comment, this same fallback feeds
`ValidateExecution`'s EV gate, a live trade-approval path, not just a display line. Six OTHER call
sites in the file already use the correct pattern (`(g_WeightsOptimized && expectedWinRate>0.1) ?
expectedWinRate : 65`) -- this was the one holdout. Fixed to match the established convention,
additively (unchanged for the case where expectedWinRate isn't populated yet). Compiled clean.

**Deep post-mortem published as an Artifact** (`tungsten_postmortem.html`, 📉 favicon) covering:
what's working (hang-fix, honesty discipline, WARRANT#56 firing live, ProbDB persistence real),
what was fixed (WARRANT#61), the honest gate-by-gate read of why goals aren't reached (with the
n=1-sample-artifact caveat on the 3 "passing" gates called out explicitly, not glossed over), and
four concrete "needs reverse engineering" open questions: (1) is the 6-component CEUS feature set
just thin on USDJPY M5 given a 29.9%/PF-0.43 UNCONDITIONED baseline from Phase 1; (2) is 9-way
regime granularity diluting sample size below what any bucket can validate on; (3) Stage-1's
already-flagged simplified-scorer gap (SLS19-TODO CRITICAL1) potentially costing real signal on a
dataset this thin, even though bounded/non-silent; (4) whether the -33.6pp drift is instrument
behavior or an artifact of this specific 21-day OOS window happening to end at a Friday-close
boundary -- GetOOSWindowBars() confirmed correctly sized (6048 bars/21 days for M5, not a truncated
window), ruling out the "OOS window too small" hypothesis I initially suspected before checking.

**Not a full tungsten-smithing pass this round** -- Manuel's "use smith and cleanup forges" request
was answered with another forge-cleanup-3 finding (WARRANT#61) plus the deep analysis; a genuine
new-capability smithing pass (forge-indicate/edge-2/4d-alpha r-stage work per the plan left at the
end of [[forge_cleanup3_seam_audit_session]]'s earlier "PAUSED" section) was not attempted this
round -- still open for a future pass, now informed by real evidence of where the actual weakness
is (feature thinness / regime granularity) rather than guessing blind.

**Not done, deliberately:** no MetaTrader/Strategy Tester run of any kind (explicit instruction) --
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
