# ARGUS COVERAGE LEDGER
**File under audit:** TUNGSTEN_10.62_A7.5_QUANT_SLS(148).mq4
**Total lines (this session, verified via `wc -l`):** 61,432
**Session:** ARGUS activation session 1 — 2026-08-22
**Pass:** 1 (first full pass, per charter Sec VIII — not yet complete)

---

## STATUS: reconciliation NOT yet achieved. Do not read this as a completed audit.

This is the ledger's **first commit**. No sector is CLOSED. The vast majority of the file is
still `UNREAD`. What follows is (a) the sector partition table this and future sessions work
against, and (b) a small number of specific, rigorously call-chain-traced regions this
activation session verified to the charter's standard (§II: "knowing what calls it, what it
calls, whether that path executes in a live run, and what changes if it does not") — everything
else in those same sectors remains `UNREAD` and the sectors themselves remain open.

**`UNREAD` line count: ~59,227 of 61,432** (updated after a second round: Sector 1 advanced from
0 to ~1,923 lines traced). The gap between that and zero is the honest measure of how much work
remains — this is still the opening of a standing, indefinite audit, not a completed pass.

---

## SECTOR PARTITION (25 sectors, ~2,500 lines each)

| Sector | Lines | Status | Notes |
|---|---|---|---|
| 1 | 1–2500 | PARTIAL | Lines 1–1923 traced this session (~77%): header/warrant-history block (1–1729, DECLARATIVE) cross-checked against current reality, not just read — see F-5/F-6 below. Lines 1924–2500 (struct definitions continuing) still UNREAD. Sector NOT closed. |
| 2 | 2501–5000 | UNREAD | |
| 3 | 5001–7500 | UNREAD | |
| 4 | 7501–10000 | UNREAD | |
| 5 | 10001–12500 | PARTIAL | Sentinel region (~10547–10650) traced this session — see findings below. Sector NOT closed. |
| 6 | 12501–15000 | UNREAD | |
| 7 | 15001–17500 | UNREAD | |
| 8 | 17501–20000 | UNREAD | |
| 9 | 20001–22500 | UNREAD | |
| 10 | 22501–25000 | UNREAD | |
| 11 | 25001–27500 | UNREAD | |
| 12 | 27501–30000 | UNREAD | |
| 13 | 30001–32500 | UNREAD | |
| 14 | 32501–35000 | UNREAD | |
| 15 | 35001–37500 | UNREAD | |
| 16 | 37501–40000 | UNREAD | |
| 17 | 40001–42500 | UNREAD | |
| 18 | 42501–45000 | UNREAD | |
| 19 | 45001–47500 | PARTIAL | Kelly ceiling region (~45343–45410) traced and repaired this session — see findings below. Sector NOT closed. |
| 20 | 47501–50000 | UNREAD | |
| 21 | 50001–52500 | UNREAD | |
| 22 | 52501–55000 | UNREAD | |
| 23 | 55001–57500 | PARTIAL | OptimizePrecisionLotSize's baseRiskPercent chain (~55910–56466) traced this session — see findings below. Sector NOT closed. |
| 24 | 57501–60000 | UNREAD | |
| 25 | 60001–61432 | UNREAD | |

**Next intended action:** claim Sector 1 (lines 1–2500), read line by line, verdict every line,
close only when zero UNREAD remain in it. Continue in order unless a specific investigation
(e.g. a pattern-library sweep, §V-6) requires jumping ahead — record any such jump and return to
sequential order afterward.

---

## CONFIRMED FINDINGS (this session, line-numbered, independently verified)

### F-1. `CalculateKellyCeiling()` — UNREACHABLE (now LIVE-VERIFIED post-fix)
- **Line 45343** (function definition). Direct grep of the entire 61,432-line file for the
  exact string `CalculateKellyCeiling` returned **exactly one match — its own definition**.
  MQL4 has no reflection/function-pointer indirection, so this is conclusive: zero call sites.
- **Verdict prior to this session's fix:** `UNREACHABLE`. WARRANT#160 (shipped earlier this
  session, before ARGUS activation) was real, correct math applied to this dead function — the
  fix itself was sound but had zero live effect. This is now on record as the session's own
  self-correction, per charter Sec VI ("report inconvenient discoveries first... including
  ARGUS's own" — extended here to the session's prior work under a different mandate).
- **Fix (this activation, same change as F-3/F-4 below):** wired in at
  `OptimizePrecisionLotSize` (~line 56209, see F-4) as a terminal minimum. Verdict now
  `LIVE-VERIFIED` for the call edge itself; the function body's internal logic verdict is
  `LIVE-VERIFIED` for lines 45343–45410 specifically (fully traced this session); the rest of
  Sector 19 is `UNREAD`.

### F-2. `g_Risk.peakEquity` — stranded high-water mark (confirmed, now live)
- **Lines 45389–45390** (only write and only read, both inside the formerly-dead function).
  Grep-confirmed no other reference exists in the file. Prior to this session's wiring fix,
  this equity high-water mark could never update — `dd` (drawdown) was permanently 0.
- Now `LIVE-VERIFIED` as a consequence of F-1's fix — the same call path activates this.

### F-3. Loss-cluster sentinel — confirmed log-truth violation (§V-3), now fixed
- **Detection (LIVE-VERIFIED):** `SentinelRecordOutcome()` (line ~10552, called live at line
  ~10645 on every closed trade) genuinely detects loss clusters and sets `g_SentinelMult`,
  printing `"stake x%.2f"` (lines ~10582, 10588).
- **Application (was UNREACHABLE, now LIVE-VERIFIED):** `g_SentinelMult`'s only consumer
  (originally line 45397, inside the dead ceiling function) meant the printed claim was false —
  the stake was never actually cut. This is a confirmed, verified instance of the pattern-library
  entry "a log asserting an action the code does not take." Fixed by the same wiring as F-1.

### F-4. The wiring fix itself (this session's change, both halves in one commit per charter Sec IX item 3)
- **`CalculateKellyCeiling()` internal fix (lines ~45383–45408):** the early return
  `if(fullKelly<=0.0) return g_Risk.minRisk;` bypassed the drawdown-aware fade and the sentinel
  multiply entirely — confirmed present, confirmed it would have converted a "no edge" verdict
  during deep drawdown into a *permanent* floor at `g_Risk.minRisk` rather than the fade-to-zero
  the function's own comment claims. Restructured so the fade computes unconditionally and
  applies to whichever base (fBase or minRisk) is correct for the edge state.
- **Wiring (line ~56209, inside `OptimizePrecisionLotSize`):**
  `baseRiskPercent = MathMin(baseRiskPercent, CalculateKellyCeiling());` — a pure terminal
  minimum (charter Sec IV Shape 1), applied after every other influence on `baseRiskPercent`,
  before `riskAmount` is computed. Provably non-regressive by construction (`MathMin` can only
  reduce, never raise).
- **Adversarial self-review performed (§VI):** hypothesized a "sticky ratchet" risk — that
  `riskMgr.currentRisk = baseRiskPercent` (line ~56465) writing back the *reduced* value could
  compound downward across trades. Traced the next call's opening lines (~55922–55927): `if
  (RiskPercentPerTrade > 0) baseRiskPercent = RiskPercentPerTrade;` unconditionally resets from
  the user's configured input on every call (true whenever the input is set, the standard case).
  **The counter-argument survived — the ratchet hypothesis does NOT hold.** Recorded here per
  the charter's explicit instruction to report a hypothesis that failed adversarial review, not
  just ones that succeeded.
- **Compile:** 0 errors, 0 warnings. **Deploy:** byte-identical (md5-verified) across
  MQL4/Experts, ELITE FIXES, x_strategies ix root. Build: SLS(148)/10.62.
- **Register impact:** this is the FIRST entry in the Capability Register (see
  `ARGUS_CAPABILITY_REGISTER.md`) — "the Kelly ceiling executes and can reduce a trade's risk
  percent" and "the sentinel's detected cut is actually applied" are now real, checkable
  capabilities where before they were documented fictions.

---

### F-5. Living-Edge/forge-indicate diagnostic cluster — self-disclosed INERT, verified consistent with its own claims
Traced `Forge_ReportSystemUnity()` (line ~38954, itself called live at line ~37947) end to end
through its full call chain: `LE_ComputeLiveCellDecision` → `LE_ComputePosteriorEdge` /
`LE_Variance` / `LE_ComputeCappedKellySize` (lines ~38890–38939), and separately
`RI_ThresholdWithHysteresis` (~38694) and `RI_LogisticSquash` (~37448) at their call site inside
`Forge_ReportSystemUnity`'s WARRANT#74/#88 extension (~lines 39002–39028). **Verdict: INERT,
confirmed — and this is the honest, self-disclosed kind, not a hidden one.** Every one of these
values (`edge`, `kelly`, `coherence`, `_hysteresisOn`, `_squashed`) is computed and fed **only**
into an `LE_Log(...)` diagnostic print — never a gate, never a size, never a threshold. The
codebase's own comments say exactly this at every site ("illustrative only, no tracked wasOn
state," "diagnostic, unwired," "NOT applied to the live score anywhere") and every claim checked
out true under trace. Contrast with the Kelly ceiling (F-1): that was undisclosed and
doctrine-contradicting dead code; this is disclosed, accurate, deliberate scaffolding. Recorded
per charter §II ("INERT... Always a finding") but the finding here is "the documentation is
correct," not a defect requiring repair.
- `LE_ComputeBracketSL`/`LE_ComputeBracketTP` (lines ~38860/38867): re-confirmed genuinely
  UNCALLED (grep: zero call sites beyond definition) — matches the original WARRANT#37 comment
  exactly, ten-plus warrants later. `UNREACHABLE`, `HELD` (pending its own dedicated wiring
  warrant per the existing comment, not this session's scope).

### F-6. Hypothesis formed and refuted: `EnableOptimalStoppingExit` documentation vs. default
Initial read of the WARRANT#89 comment block ("Gated HARD OFF by default") against the actual
input declaration (`input bool EnableOptimalStoppingExit = true;`, line 1667) looked like a
documentation/reality mismatch — worth flagging as a candidate finding. **Did not survive
adversarial review**: the very next line records `WARRANT#90 (2026-07-22): activated per
Manuel's go-ahead` — the comment preserves the original ship-state description (accurate at
WARRANT#89) alongside the later, explicitly-authorized change (WARRANT#90), rather than silently
overwriting history. `ShouldExitOnOptimalStopping()` (line ~38523, called live at ~19584 gated
on this same input) is genuinely `LIVE-VERIFIED`, not a defect. Recorded per charter §VI's
explicit instruction to report a hypothesis that failed review, not only ones that succeeded.

---

## HELD ITEMS (defect known, repair deliberately deferred — reason recorded)

### H-1. `RepairWeakRegime`'s dead self-repair path
Per charter Sec III: "Anything touching RepairWeakRegime's dead self-repair path... This gate
does not open." Confirmed still present (bar-collection cap of 300 vs. an n>=500 evidence floor,
making it a structural no-op) as of prior sessions this week. Not re-verified line-by-line this
activation — flagged HELD, not re-opened, per explicit charter instruction. Five prior live
hangs (#20/#31/#103/#134) are the standing reason.

### H-2. The Consolidated intelligence cluster (pass_151 finding D)
`ConsolidatedMarketAnalysis()`/`ConsolidatedPatternRecognition()` and their cluster
(`CalculateEnhancedProbability`, `PredictPatternFormation`, `ForecastRegimeChanges`,
`UpdateNeuralNetworkSimulation`, `CalculateCompositeScore`, `CalculateCorrelationRisk`,
`CalculateIntelligentRisk`, `IsBuffaloSetup`) — fully implemented, forward-declared as if
load-bearing, zero call sites anywhere (confirmed via the new V-4/V-5 instrument, pass_151).
UNLIKE H-3/finding A/finding B, no live superseding replacement was found or verified — this is
confirmed disconnected, NOT confirmed redundant, and is potentially real lost capability
(a neural-network-simulation / regime-forecast / composite-scoring / correlation-risk layer).
HELD pending a dedicated pass with its own forge-4d-alpha hardening review — the single largest
open item this ledger currently tracks. Disclosed in-source at `ConsolidatedMarketAnalysis()`.

### H-3. `UpdateAdaptiveGates()` — reachable but inert (pass_151 finding C)
Called live once per day (OnTick's "Update adaptive gates daily" site) but its body is a bare
`return;`. Its neighbors `IsCurrentHourDisabled()`/`GetSmartThresholdForCurrentHour()`/
`GetCurrentThreshold()` — fully implemented, bounded (-3/0/+3/+6/+10) hour-of-day threshold
adjustment off real, live-tracked per-hour win-rate data — are themselves also zero-call-site.
No prior warrant comment records what this function's body used to be, so an implementation was
NOT reconstructed this pass (would be a guess dressed up as a repair). HELD pending a dedicated
pass. The GMT-correction gap found inside its neighbors WAS fixed this pass (WARRANT#166,
pass_152) so the landmine is retired before that dedicated pass has to rediscover it.

---

## NEXT SESSION RESUMES HERE

- Sector 1 (lines 1924–2500, the remainder) is the next claim, per charter Sec II
  ("partitioned... claimed, read line by line, verdicted, and closed... in order"). Do not
  re-read 1–1923 — already traced and recorded above. NOT read this session (2026-08-25's pass
  used the V-4/V-5 instrument for a whole-file reachability sweep instead of continuing the
  sequential sector read — both are legitimate charter tools per Sec V, but Sector 1 itself is
  still exactly where pass_150 left it).
- V-4/V-5 (total call graph + global reachability) are now BUILT and re-runnable (pass_151,
  2026-08-25) — see `ARGUS_CAPABILITY_REGISTER.md` R-9. V-1 (reachability heartbeat, a *runtime*
  self-test rather than this static tool) is still not built.
- Two new HELD items opened this session: H-2 (Consolidated intelligence cluster — largest open
  item in this ledger, dedicated pass needed) and H-3 (`UpdateAdaptiveGates()` stub — dedicated
  pass needed, GMT landmine under it already retired via WARRANT#166).
- Capability Register: R-9 and R-10 added this session (both CHECK BUILT AND PASSING). R-1
  through R-6 still NAMED, CHECK NOT BUILT — still open work.
