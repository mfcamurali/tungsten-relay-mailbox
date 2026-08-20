# TUNGSTEN — Current Problem Areas
### Strategic targets for workarounds · grounded in 10.40 SLS(126) + live run observations
*Not theoretical — every item below is evidenced in the codebase, the live run log, or the warrant trail.*

---

## 1. SPARSE REGIME COLLAPSE
**What:** 5 of 9 regimes (Bullish Reversal, Bearish Reversal, Range, Choppy, Building Momentum) flatlined at val=0.0% with zero movement across all P3B search stages on USDJPY M5. Weights literally unchanged from start to finish. The system can only truly trade in 3 regimes (Strong Bull, Strong Bear, Controlled Pullback).
**Root:** Not enough historical examples of these regime types on this instrument/timeframe for calibration to learn anything real. The sparse-seed fallback (lines ~5338–5351) gives them a structurally-informed prior but it's a guess, not learned evidence.
**Why it matters:** The system is blind in 5 of 9 market states. When the market enters one of those states, it's trading on a prior that was never validated — or standing down entirely and missing opportunity.
**Workaround targets:**
- Cross-instrument seeding: calibrate sparse regimes on correlated instruments (e.g. XAUUSD for gold-like momentum regimes) and transfer with a discount factor
- Longer history windows or multi-timeframe aggregation to gather more regime samples
- Synthetic regime augmentation: use the regime classifier to label bars across multiple symbols and pool the evidence
- Honest fallback: if a regime truly can't be calibrated, enforce a hard stand-down with explicit "insufficient evidence" status rather than trading on a seed

---

## 2. DUAL SCORER PATHS (LEGACY vs ENHANCED)
**What:** Two separate scoring engines coexist — `CalculateScoreWithWeights` (the "simplified" legacy scorer) and `CalculateEnhancedUnifiedScore` (the real one). The SLS19-TODO at line ~7766 flags this as CRITICAL: Stage -1 isolation scan still uses the simplified scorer while everything else uses Enhanced.
**Root:** The Enhanced scorer was built alongside the legacy one rather than replacing it. Both survived, creating a seam where calibration decisions (Stage -1) are made with one scorer but executed with another.
**Why it matters:** If the two scorers rank signals differently — and they will, because they weight differently — then what calibration learns in Stage -1 doesn't transfer to live. The EA optimizes against one objective and trades against another. This is a class of "misaligned logic" (root cause #3 from Forge Sword).
**Workaround targets:**
- Unify to one scorer everywhere — Enhanced replaces legacy, no exceptions
- If legacy must survive for a specific diagnostic purpose, isolate it behind a clearly-labelled diagnostic-only flag that never touches a live weight
- Verify that every calibration stage and every live decision path calls the same scorer by tracing call sites exhaustively

---

## 3. LOG MECHANISM: OVERWRITE-NOT-APPEND
**What:** `TLog()` opens the live log with `FILE_WRITE` (line 7201), which overwrites the file on every call. Two TLog calls landing within the same 5-second external poll window means the earlier one is silently lost.
**Root:** `FILE_WRITE` truncates; `FILE_WRITE|FILE_READ` or `FILE_READ|FILE_WRITE` with seek-to-end would append. Simple flag error, but it has downstream consequences.
**Why it matters:** The live run already demonstrated this — some P3B stages (e.g. r2's ascent-200) never appeared in the watcher feed even though they executed. You can't diagnose what you can't see. This also violates the Forge Sword requirement for full decision-reconstructability (§8.3 / WARRANT#137).
**Workaround targets:**
- Change `FILE_WRITE` to an append pattern (open with seek-to-end, or accumulate in a global string buffer and write once per bar)
- Add a rolling log rotation (e.g. keep last N KB) to prevent unbounded file growth
- Separate the human-readable TLog from the structured decision log — the structured one appends always, the human one can rotate

---

## 4. SILENT PROGRESS GAPS (THE RECURRING CLASS)
**What:** A 6+ minute stretch after P3B produced zero log lines while CPU kept climbing. Same class as WARRANT#20, #134, #141 — previously found and fixed at other call sites, but the pattern keeps recurring at new ones.
**Root:** Any CPU-bound loop without a TLog inside it is invisible to an external watcher. The fix has been applied reactively (add TLog at the specific site that was found silent), but the pattern isn't guarded against structurally.
**Why it matters:** Indistinguishable from a hang. You can't tell "working hard" from "stuck." This is also the class that makes the 60-minute timed watch unreliable — if a 6-minute silence falls inside the window, the watcher reports "no activity" when the system is actually progressing.
**Workaround targets:**
- Structural guard: every loop that runs > N iterations or > M seconds must emit at least one progress TLog per interval (e.g. every 30 seconds or every 10% of expected iterations)
- A watchdog timer that flags any gap > threshold as a potential silent-progress issue, rather than waiting for a human to notice
- Audit every remaining CPU-bound loop (there's a finite list) and add progress logging to all of them in one pass, not one at a time as they're discovered

---

## 5. RAW-RETURN vs SIMULATED-OUTCOME MISMATCH (WARRANT#136 / #145)
**What:** INDINTEL and early calibration stages rank indicators by raw return (signed R-multiple), but the actual trading outcome depends on simulated TP/SL execution. The two can disagree — an indicator that looks good by raw return may look bad when TP/SL are applied, and vice versa.
**Root:** The indicator intelligence pass was built to rank by raw price movement. TP/SL simulation was added later. The two were never reconciled into one consistent ranking.
**Why it matters:** The system may over-weight indicators that look good in raw terms but underperform under actual execution constraints, or under-weight ones that look weak in raw terms but catch the right moves within the TP/SL window. WARRANT#145 (build 127) is described as the "real architectural fix" for this — needs verification.
**Workaround targets:**
- Verify that 127's fix actually closes this: does INDINTEL now rank by simulated outcome, not raw return?
- If both metrics are kept, make the simulated-outcome ranking the authority for live weights, with raw return as a diagnostic-only secondary view
- Ensure WARRANT#142's trim logic (Stage 4 TP/SL evidence trimming Stage 1-3 raw-return weights) is downstream of the reconciliation, not a separate compensating patch

---

## 6. PHASE-TO-PHASE HOLDOUT CONTAMINATION RISK
**What:** Multiple calibration phases split data into train/holdout sets. If they don't all use the same split convention, a threshold fit on Phase 2's in-sample data could be re-tested on Phase 3's in-sample data that overlaps with Phase 2's holdout — a subtle leak.
**Root:** The phases were built incrementally over years. Each phase's holdout logic was written independently.
**Why it matters:** Holdout contamination inflates validation scores. The system thinks it has more edge than it does. This is one of the hardest bugs to find because the numbers look *good* — they're just not honest.
**Workaround targets:**
- Enforce one global holdout split (70/30 chronological) shared by all phases — defined once, referenced everywhere
- Add an assertion that no bar index appearing in any phase's training set also appears in any phase's validation set
- The Forge Sword annex (§C, rule C1) already specifies this — verify it's implemented, not just specified

---

## 7. CALIBRATION TIMEOUT BEHAVIOUR
**What:** Phases have time budgets (90s for INDINTEL, longer for P3B). When a phase hits its budget, it truncates — but the live run showed phases completing well inside budget (0.7s for INDINTEL) on some instruments while potentially timing out on others.
**Root:** Budget was set for gold's bar count and complexity. Different instruments or longer histories may exceed it. The truncation path must not write partial results that look complete.
**Why it matters:** A truncated phase that writes partial weights as if they're final will poison every downstream phase. The system doesn't know its calibration was incomplete.
**Workaround targets:**
- Mark truncated results with an explicit `TRUNCATED` flag that downstream phases check before consuming
- Scale budgets to actual bar count / instrument complexity rather than hard-coding
- If a phase truncates, fall back to the last complete calibration's values rather than using the partial ones

---

## 8. CHECKPOINT CLOBBER ON RESUME
**What:** The observations file notes this as a documented past bug — checkpoint/resume of a long phase (P3B outer loop) could overwrite valid estimates with partials.
**Root:** Resume logic replaced rather than merged.
**Why it matters:** A terminal crash mid-calibration followed by a resume could leave the system with worse parameters than it started with — the exact opposite of what recovery should do.
**Workaround targets:**
- Verify that the current build's checkpoint logic merges rather than clobbers (the annex §E5 specifies this)
- Add a pre/post checkpoint integrity check: the restored state must be at least as complete as the pre-crash state
- Keep last N=3 good checkpoints so there's always a known-good fallback

---

## 9. SPREAD/COST CALIBRATION LAG
**What:** The live run confirmed the line: "spread not yet calibrated this run — COST-UNVALIDATED." Until spread calibration completes, the system doesn't know whether execution costs invalidate the edge.
**Root:** Spread calibration requires observed ticks, so it can't run until after the EA has been live for a while. During that window, entries are either blocked (safe but misses opportunity) or allowed without cost validation (risky).
**Why it matters:** On gold especially, spreads can swing from 15 to 80+ pips around news. Trading in the uncalibrated window with a wide spread could wipe the edge on every entry.
**Workaround targets:**
- Seed spread estimates from historical tick data or broker-reported typical spreads at init, then refine online
- Hard-block entries until a minimum spread sample is gathered (e.g. 50 ticks), rather than trading cost-unvalidated
- Regime-aware spread ceilings: the news-blackout window (events CSV) should automatically tighten the spread gate

---

## 10. FORGE INDICATOR RELIABILITY CURVE NOT YET CALIBRATED
**What:** The newly forged F1-F4 indicators (WARRANT#135) are wired in, but the live run showed: "reliability curve not yet calibrated (insufficient resolved samples)."
**Root:** The indicators were just integrated — they haven't seen enough trades to build their IC/reliability profile. This is expected and correct behaviour (the abstain-until-evidence rule), but it means the new indicators aren't contributing yet.
**Why it matters:** The signal breadth improvement Forge Sword was built for isn't active until the indicators earn their weight through enough observed outcomes. Until then, the system is running on the same signal base as before.
**Workaround targets:**
- Accelerate evidence gathering by running on demo across multiple instruments simultaneously
- Use ghost/shadow evaluation to let the indicators build their reliability curve on historical data before requiring live confirmation
- Set a realistic timeline expectation: IC calibration needs N trades per regime per indicator — at current trade frequency, estimate how many days/weeks that takes

---

## PRIORITY ORDER (by impact × fixability)

| Priority | Problem | Impact | Fix complexity |
|---|---|---|---|
| **P0** | #2 Dual scorer | Misaligned calibration→live | Medium — unify call sites |
| **P0** | #3 Log overwrite | Blind to own behaviour | Low — one flag change |
| **P1** | #5 Raw vs simulated | Wrong indicator ranking | Medium — verify #145 |
| **P1** | #6 Holdout contamination | Inflated edge estimates | Medium — one global split |
| **P1** | #1 Sparse regimes | Blind in 5/9 states | High — needs data strategy |
| **P2** | #4 Silent gaps | Can't distinguish working from stuck | Medium — audit all loops |
| **P2** | #9 Spread lag | Cost-blind entries | Medium — seed + gate |
| **P2** | #7 Calibration timeout | Partial results consumed as final | Medium — flag + fallback |
| **P3** | #8 Checkpoint clobber | Recovery worse than crash | Low — verify current logic |
| **P3** | #10 Forge indicator ramp | New signals not contributing yet | Low — expected, just needs time |
