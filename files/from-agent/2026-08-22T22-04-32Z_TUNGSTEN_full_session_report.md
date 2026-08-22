# TUNGSTEN — Full Session Report, All Targeted Upgrades
## 2026-08-22 — sent alongside source/ex4/ledger/ARGUS artifacts

**Final build:** TUNGSTEN_10.62_A7.5_QUANT_SLS(148) — compiles 0 errors/0 warnings, deployed
byte-identical (md5-verified) to MQL4/Experts, ELITE FIXES, and x_strategies ix root.
**Session started at:** SLS(138)/10.52, pass_139.
**forge_ledger.json:** through pass_150.

This session ran two distinct disciplines back to back: (1) three Prometheus+Sword
low-performance-elimination campaigns (WARRANT#157-165, sampling-based, targeted), then
(2) first activation of a new standing charter, ARGUS (total-coverage, not sampling), which
immediately found one of this session's own campaign-1 fixes had shipped onto dead code.

---

## PART 1 — Prometheus + Sword campaigns 1-4 (WARRANT#157-165)

### WARRANT#157 — Insufficient evidence (indicator weighting)
`g_IndWeight[k]` synthesis let an indicator with ZERO measured directional evidence still cast
a real directional vote in the unified score, purely off its amplitude-IC term (magnitude
correlation — orthogonal to direction). Fixed: the amplitude term now only amplifies an
already-proven weight, never manufactures one alone.

### WARRANT#158 — Misaligned logic (TP/SL execution seam)
`CalculateSmartTPSL()`'s broker-min-stop-distance fallback pulled its RR ratio from a wholly
separate, non-regime-aware heuristic loop instead of the regime/session/Hurst-calibrated ratio
this exact function had just computed for this exact trade. Fixed to reuse the trade's own
calibrated ratio.

### WARRANT#159 — Dead/unreachable path (pattern learning)
The 100-slot pattern-sequence library had no eviction policy — a confirmed-poor predictor could
squat a slot forever. Fixed with quality-based eviction (evicts only proven-poor AND
past-its-trial-period residents).

### WARRANT#160 — Mathematical error (Kelly ceiling formula) — see Part 2 for the rest of this story
`CalculateKellyCeiling()`'s win-rate floor was 0.50 — for any realistic reward:risk, that made
the formula's own "no edge -> minimum only" branch mathematically unreachable. Lowered floor to
0.10 so a genuine bad patch is actually recognized. **This fix later turned out to have zero
live effect at the time it shipped — see WARRANT-ARGUS-1 below. The formula fix itself was
correct and is still in the code; what was missing was the wiring, fixed later the same day.**

### WARRANT#161 — Misaligned logic (ProbDB extrapolation)
Sparse-bucket extrapolation claimed "most similar populated pattern" but never filtered by score
strength. Added a +/-1 scoreRange similarity filter.

### WARRANT#162 — Dead/unreachable path (signal-quality gate) — strongest campaign-1-4 finding
`signal.confidence`'s floor (0.50) sat above `ENHANCED_SIGNAL_QUALITY_THRESHOLD` (0.45) — whose
own comment records real historical values as low as 0.26. The floor had made a real 4-gate
entry filter silently operate as 3 gates for every signal. Lowered floor to 0.05.

### WARRANT#163/164/165 — GMT-correction convention, mechanical sweep
This file enforces a GMT-time correction at ~35 sites. 3 session/hour-bucketing call sites
silently skipped it: `DetermineSession()` (9 downstream call sites, broadest impact), a live
per-hour historical-WR conviction gate, and a diagnostic log label (lowest severity). All fixed
at their origin, reusing the established correction idiom.

### Campaign 4 ("keep going until no more fixes possible")
Surveyed 7 more angles (remaining floor sites, a dead constant, the WARRANT#109-flagged
14+-hardcoded-bracket backlog, alignment-score chain, CEO risk ceiling, 3 spread monitors, the
livePF shortcut) — came back genuinely clean. Logged honestly rather than manufacturing a fix.

---

## PART 2 — ARGUS activation: the Kelly ceiling had never executed

A new standing charter, `ARGUS_CHARTER.md`, was activated — total-coverage line-by-line
verdicting, not sampling. Its own opening justification named a specific, checkable claim:
`CalculateKellyCeiling()` — the entire Kelly-sizing ruin-prevention mechanism — had **zero call
sites** anywhere in the file.

**Independently verified via direct grep (conclusive in MQL4 — no reflection): TRUE.** WARRANT#160
above, shipped hours earlier this same session, was real correct math applied to a function
nothing ever called. Also confirmed dead in the same blast radius:
- `g_Risk.peakEquity` — a stranded high-water mark, read/written only inside the same function.
- The loss-cluster sentinel — `SentinelRecordOutcome()` genuinely runs live and prints
  `"stake x0.XX"` on every detected break, but its multiplier's only consumer lived inside the
  same dead function. **The print was true. The stake was never actually cut.**

Worth stating plainly: this session's own campaign-4 "clean audit" pass had *already* re-checked
this exact function's internal math against WARRANT#160 and called it sound, without ever
checking whether the function was reachable. That is the precise blind spot a sampling campaign
cannot see past, and the reason ARGUS exists.

**Fixed same day, two changes in one commit (per the charter's explicit requirement — revive and
fix the internal bug together, never separately):**
1. `CalculateKellyCeiling()`'s early return (`if(fullKelly<=0) return g_Risk.minRisk;`) bypassed
   the drawdown-aware fade and the sentinel multiply entirely. Restructured so the fade always
   applies, to whichever base (fBase or minRisk) fits the edge state — a "no edge" verdict during
   a real drawdown now still fades toward zero instead of freezing at a flat floor.
2. Wired into `OptimizePrecisionLotSize` as a pure terminal minimum:
   `baseRiskPercent = MathMin(baseRiskPercent, CalculateKellyCeiling())` — provably
   non-regressive by construction (`MathMin` only ever reduces).

**Adversarial self-review performed and one hypothesis killed by evidence:** worried the
Kelly-reduced risk% could compound downward across trades via `riskMgr.currentRisk`. Traced the
next call and found `baseRiskPercent` unconditionally resets from the user's `RiskPercentPerTrade`
input every time — the ratchet hypothesis does not survive and is recorded as a failed
hypothesis, not a finding.

Build: SLS(147)->SLS(148)/10.61->10.62. Compile 0/0. Deployed byte-identical everywhere.

---

## PART 3 — ARGUS sector work (Sector 1, ~1,923 of 2,500 lines traced)

No source changes this round — pure verification. Two results worth recording:
- **Living-Edge/forge-indicate diagnostic cluster** (`Forge_ReportSystemUnity` and its call
  chain) verdicted INERT — but *honestly self-disclosed* as diagnostic-only in its own comments.
  Every claim checked out true. Contrast with the Kelly ceiling: this one was never
  misrepresented as live.
- **A hypothesis formed and refuted:** `EnableOptimalStoppingExit`'s comment said "HARD OFF by
  default" while the input defaults `true` — looked like a mismatch until the very next line
  showed a later warrant explicitly activated it with Manuel's authorization. Not a finding.

`LE_ComputeBracketSL`/`TP` re-confirmed still genuinely uncalled, unchanged status, HELD.

---

## What this IS and IS NOT

**Is:** 10 specific, individually-traced-to-root-cause, diff-verified, compile-clean,
byte-identically-deployed fixes this session (WARRANT#157-165 plus the ARGUS Kelly-ceiling
wiring), plus the start of a genuinely different, total-coverage audit discipline layered on top
of the sampling one — with its own persistent ledger (`ARGUS_COVERAGE_LEDGER.md`) and capability
register (`ARGUS_CAPABILITY_REGISTER.md`), both included in this send.

**Is NOT, and was never claimed to be:**
- "Every mathematical flaw fixed." ARGUS's own coverage ledger currently shows ~59,227 of 61,432
  lines still `UNREAD`. Zero sectors are closed. This is session 1-2 of an indefinite standing
  audit, not a finished one.
- `RepairWeakRegime`'s dead self-repair path remains deliberately un-fixed — the charter itself
  names this gate as one that does not open regardless of what else is found, given five prior
  live hangs (#20/#31/#103/#134).
- Live-tested. Every fix here, including the Kelly-ceiling wiring, is unverified against a real
  market tick. The market has not been open since these shipped.

Per the codebase's own PROMETHEUS_CAPABILITY_CHARTER.md closing clause: none of this is proof of
profit. It is real, checkable improvement to how correctly and honestly the system reasons about
its own risk and evidence. The market decides the rest.

**Files included in this send:** TUNGSTEN_10.62_A7.5_QUANT_SLS(148).mq4/.ex4, forge_ledger.json
(through pass_150), ARGUS_COVERAGE_LEDGER.md, ARGUS_CAPABILITY_REGISTER.md, and this report.
