# ARGUS CAPABILITY REGISTER
**Purpose:** every faculty TUNGSTEN possesses, each with an executable check that demonstrates
the faculty still functions. Per charter Sec IV: "the register grows, never shrinks. Retiring an
entry requires Manuel." Every build should run the full register; a build that loses an entry
does not ship, regardless of what it fixed.

**Status this session:** seeded with the charter's own minimum list plus this session's new
entry (R-8). Entries R-1 through R-6 are named per the charter but their executable checks are
NOT yet built — that is explicit, tracked work, not a claim they exist. Do not read a named entry
as a verified-passing entry unless its row says CHECK BUILT.

---

| ID | Capability | Executable check | Status |
|---|---|---|---|
| R-1 | Each of the four entry gates fires and is capable of refusing | Not yet built — needs a harness that feeds a known-bad synthetic signal through each gate and asserts it refuses, plus a known-good one and asserts it passes | NAMED, CHECK NOT BUILT |
| R-2 | The overfitting check rejects an overfit candidate | Not yet built — needs a synthetic overfit candidate (e.g. in-sample-only edge, fails OOS) fed to the CSCV/PBO machinery with an assert on rejection | NAMED, CHECK NOT BUILT |
| R-3 | The reversal trim's evidence floor holds | Not yet built — needs an assert that the n>=500 (or current documented floor) sample-size gate on the inversion-trim mechanism actually blocks below-floor activation | NAMED, CHECK NOT BUILT |
| R-4 | The ratchet refuses a worse challenger | Not yet built — needs a synthetic worse-scorecard fed to `ForgeRatchetPromote()` with an assert on `false` return AND no champion mutation | NAMED, CHECK NOT BUILT |
| R-5 | Compounding permission granted on a clean first-attempt calibration | Reference: WARRANT#153 (this session's prior work, pre-ARGUS) fixed `g_PRI[6].armed` semantics for exactly this case. Executable check not yet built — needs a synthetic clean-first-attempt calibration run with an assert that `g_Compounding.isActive`/`_preCalibOk` end up true | NAMED, CHECK NOT BUILT |
| R-6 | Every persistence path survives a save/load round trip | Reference: WARRANT#116 (memory-corruption fix, prior session). Executable check not yet built — needs a scripted save-then-load with a full struct-field diff asserting zero drift | NAMED, CHECK NOT BUILT |
| R-7 | The sentinel's detected loss-cluster actually cuts the stake | **CHECK BUILT AND PASSING as of this session.** Prior to today: `g_SentinelMult` was set by `SentinelRecordOutcome()` (line ~10552, live-called line ~10645) but its only consumer lived inside the then-dead `CalculateKellyCeiling()` — the print (`"stake x%.2f"`) was true, the cut was not (log-truth violation, charter §V-3). Fixed this session by wiring `CalculateKellyCeiling()` into `OptimizePrecisionLotSize` as a terminal minimum (line ~56209) — the sentinel's multiply (line ~45406) is now on a live path. Check: confirm via grep that `CalculateKellyCeiling` has a real call site (currently exactly one, at `OptimizePrecisionLotSize`) and that the call is unconditional on that path. Re-run this grep-check on every future build — if the call site count ever returns to zero, this entry regresses and the build does not ship. | **CHECK BUILT — PASSING** |
| R-8 | The preservation ceiling (Kelly ruin-prevention) executes and can only ever reduce a trade's risk percent, never raise it | **CHECK BUILT AND PASSING as of this session.** Verified by construction: the wiring is `baseRiskPercent = MathMin(baseRiskPercent, CalculateKellyCeiling())` — `MathMin` cannot increase a value, so this cannot regress sizing upward under any input. Verified `CalculateKellyCeiling()`'s own output is bounded `[0.0, KellyMaxFraction]` (final clamp, line ~45409), so no pathological (negative/NaN/unbounded) value can reach the terminal minimum. Re-check on every future build: grep for the exact wiring line and confirm the clamp direction (`MathMin`, not `MathMax`) is unchanged. | **CHECK BUILT — PASSING** |
| R-9 | V-4/V-5 (total call graph + global reachability): every function is either reachable from OnInit/OnTick/OnDeinit or its non-reachability is a DISCLOSED, ledger-recorded finding, never a silent surprise | **CHECK BUILT AND PASSING as of pass_151 (2026-08-25).** A standalone Python static-analysis script (function-def parser + brace-matched body extraction + caller/callee graph + BFS from the 3 entry points) — the two instruments the charter named as higher-leverage than more point-fix hunting, now real and re-runnable. Cross-validated against ARGUS's own known findings before trusting it (correctly re-derived the already-confirmed Forge_ReportSystemUnity chain and LE_ComputeBracketSL/TP as unreachable, zero false negatives on known cases). First real run found 73 unreachable / 22 zero-global-call-site functions; 4 were manually traced to real findings this pass (2 confirmed-superseded/HELD, 1 confirmed dead-but-reachable stub, 1 confirmed large orphan needing dedicated scoping — see pass_151/forge_ledger.json). Re-run this script on every future build; a NEW unreachable function appearing that is not immediately disclosed in-source is a regression of this entry. | **CHECK BUILT — PASSING** |
| R-10 | Every hour-of-day bucketing site in the file uses the same GMT-corrected convention — no site silently indexes a different "hour" than the rest of the system means | **CHECK BUILT AND PASSING as of pass_152/WARRANT#166 (2026-08-25).** WARRANT#163-165 (2026-08-22) fixed 3 sites; this session's V-4/V-5-driven audit found and fixed a 4th (`RecordComprehensiveSignal`'s `sig.hourOfDay`, plus the two dead readers `IsCurrentHourDisabled`/`GetSmartThresholdForCurrentHour`). Check: `grep -c "TimeHour(TimeCurrent())" ` sites not immediately followed by `- g_ServerTimeOffsetHours` should be zero outside of the offset-computation site itself (line ~17534, which legitimately reads the raw broker hour to *derive* the offset). Re-run this grep on every future build that adds a new hour-of-day read. | **CHECK BUILT — PASSING** |

---

## How to re-run this register
Until a proper automated harness exists (R-1 through R-6), the checks marked CHECK BUILT are
static/grep-verifiable by construction — re-run the specific grep/read described in each row
against the current build before shipping any further change that touches the same functions.
The NAMED-but-not-built rows are open work: each needs a real synthetic-input test, not a
read-through, before it can be marked CHECK BUILT.

**Never remove a row from this table.** Downgrading a row's status (e.g. CHECK BUILT →
regressed) is expected and required if a future change breaks it — that downgrade IS the
register doing its job. Removing the row entirely is not permitted without Manuel.
