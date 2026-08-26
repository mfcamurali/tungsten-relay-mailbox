# SWORD II — Status (live document, overwritten each pass)

**Last updated:** 2026-08-26, resumed post-restart (pass_179), per Manuel's explicit "don't stop,
run indefinitely, fix→test→observe→repeat" loop instruction, now explicitly extended to include
dense external research per open problem area, curated/adapted per Part X's D1–D7 protocol (not
blind adoption). Read `SWORD_II_MASTER.md` for the doctrine this implements; read
`# EX MACHINA\...\ELITE FIXES\forge_ledger.json` (pass_158 onward) for the full detailed record.
This file is the 30-second version.

> **RUNNING (pass_179).** Post-restart: terminal relaunched clean, correct build confirmed
> (WARRANT#176-179 markers present, byte-identical MD5 across all 3 deploy locations), live
> calibration progressing normally (PHASE 1 → 2 → 3B). WARRANT#180 (per-regime IC/AUC breakdown,
> the queued next step) is done — see below. Say **"sword master tungsten"** to continue the loop.

## HEADLINE NEW RESULT (2026-08-26, WARRANT#180): the per-regime breakdown is done, and it's ALSO null

Ran Part VI.1-R2 against WARRANT#179's regime-tagged export (`research_layer/
analyze_regime_breakdown.py`, reusing WARRANT#178's G-SELF-tested IC/AUC primitives). 5 of 9
regimes cleared the 3,000-sample floor (Strong Bull n=18,050, Strong Bear n=10,223, Bullish
Reversal n=3,255, Choppy n=5,695, Building Momentum n=4,703); every one reads at/near null —
IC in [-0.0079, +0.0222], AUC in [0.4952, 0.5135], none distinguishable from zero even before
DSR/multiplicity correction. **Real conclusion: the pooled null (WARRANT#178) is not hiding
regime-conditional structure that Part VI.0's "averaging across a sign-flip" concern would
predict.** This is evidence toward "components genuinely lack discrimination" over "the
measurement is mis-specified" — the two candidates Part VI.1-R3 exists to distinguish. Strong
Bear's cell here (34.29% WR, near-null IC/AUC) is independently consistent with — but
methodologically distinct from — WARRANT#176's live forward/reverse dir-check (36% vs 47% WR);
both point the same direction without being the same test.

**New research-derived next step (T0-1h, not yet built):** the historical export captures only
the final blended score, not the ~17-23 raw per-indicator readings. Literature on meta-labeling
(López de Prado; confirmed current 2026-08-26) is explicit that a nonlinear secondary/meta-model
earns its "information advantage" specifically when the primary signal is linear — ours is a
linear weighted blend. VIII.4 step 6 (the meta-model) therefore cannot yet be run meaningfully:
trained on the blended score alone, it can't discover anything the linear blend didn't already
express. **Next MQL4 change queued: extend the export to raw per-indicator values — deliberately
not started while this calibration run is active**, same standing rule as CEA/pathstate work.
Also reconfirmed this pass: `purged-cross-validation` (eslazarev) and `skfolio`'s
`CombinatorialPurgedCV` are both still actively maintained as of 2026 — VIII.3's tooling call
stands, not stale.

## LATEST (pass_184-185, 2026-08-26): four named dead ends, each actually resolved

Per Manuel's "need working solutions for every dead end, not just documentation of them":

1. **WARRANT#184 (shipped, code):** the fixed-bracket export made magnitude-IC mathematically
   identical to won/lost IC (proven pass_183). Added `mfe_atr`/`mae_atr`/`bars_to_mfe`/
   `bars_to_mae`/`r_continuous` to the historical export — every row, including previously-
   dropped unresolved ones, now gets a real continuous R. `TUNGSTEN_10.64_A7.5_QUANT_SLS(150)`,
   compiled 0/0, deployed byte-identical (MD5 `86b8d89e57aa52943c280ec94f56041b`). Caught and
   self-corrected a mid-edit mistake (briefly corrupted the already-shipped SLS(149) source file)
   — restored from the untouched, verified root/Experts copies rather than hand-patched.
2. **G-SELF, "registry not enforcement" (shipped, code):** `gate_self()` existed since pass_161
   but nothing ever called it. Built `validate_finding()` in `cerberus.py`, composing all four
   applicable gates into one real accept/reject decision, self-tested against the exact
   F6/V-4-V-5 incident shape plus a compounded-failure case. Scope stated honestly: validates a
   Finding object; migrating `forge_ledger.json` itself to structured records is separate,
   larger future work, not silently claimed done.
3. **`purgedcv` "not installed" (resolved):** installed `purgedcv-0.1.4` and `skfolio-1.0.0`,
   then validated both with real known-answer checks (not just trusting `pip`) —
   `CombinatorialPurgedCV` produces exactly C(6,2)=15 paths in both independent implementations,
   `deflated_sharpe_ratio` correctly crushes significance 0.95→0.00 as trials go 1→100. All 5
   newly-validated instruments registered into cerberus's G-SELF registry.
4. **Per-component IC visibility** — see WARRANT#182 below, already shipped this session.

All 10 cerberus self-tests + the full `run_cerberus.py` pipeline re-verified passing after
every change.

## PRIOR (pass_183, 2026-08-26): SWORD III installed, export audited, real fix shipped

**SWORD_III.md installed** — the correction campaign (builds on this doc, doesn't replace it).
Its blocking Part I (audit the evidence before building on it) is now substantially closed:
export join logic code-audited clean, I-2's shift anomaly fully explained (autocorrelation from
overlapping lookahead windows, not a bug — `IC(won[t],won[t+1])=0.68`), 3.6's "magnitude IC"
proven mathematically degenerate on the current fixed-bracket export (can't add information,
needs continuous R — same blocker as per-component IC).

**WARRANT#182 (real fix, shipped, no live test yet):** found `g_RegimeIC[9][6]` — per-component
(mtf/momentum/volume/volatility/session/pattern) IC per regime — was already computed and
already consumed live every calibration run (drives weight gating), but its diagnostic log line
was silenced by `g_CalibSilent` on every real run. One `TLog()` call restores it to
`TUNGSTEN_live.log` with zero new export pipeline. **This directly answers SWORD III Part 3.1's
decision point on the next calibration run** — no new schema needed. WARRANT#183: flipped
`ExportHistoricalScoreOutcomes` back to `false` (its job is done). Shipped as
`TUNGSTEN_10.63_A7.5_QUANT_SLS(149)`, compiled 0/0/666ms, deployed byte-identical (MD5
`1a1d59522ae6b9bbbb1b278592923979`) to all 3 locations. **terminal.exe NOT relaunched** — per
explicit "no live testing yet."

## ALSO THIS PASS (WARRANT#181, pass_180): a stale-register correction, found live

Tonight's calibration itself surfaced a documentation/reality gap: the live log showed a full
Bailey & Lopez de Prado CSCV overfitting check firing and correctly rejecting an overfit weight
candidate (`PBO-CSCV 0.800 > 0.50 → regularized 35%`, regime 3). Traced to WARRANT#79
(2026-07-19) — R-2 ("overfitting check", listed in the master doc as "NAMED, CHECK NOT BUILT")
is actually built and has been live for over a month; the master doc's own register was stale.
Corrected in `SWORD_II_MASTER.md` II.3/II.5/VIII.0. Caveat: it's scoped to Phase 3B's per-regime
weight search, not yet a general instrument for the future CEA meta-model — but extending an
already-working instrument is materially cheaper than VII.6's "build R-2" implied starting from
zero.

## PRIOR RESULT (pass_176-178): the real pooled IC/AUC test

After 7 live restart cycles all reaching STAND DOWN with a near-identical Phase 1 diagnosis
(~28-29% WR, "barely above random"), built a historical-bar export (WARRANT#177) that computes
the blended score + a mechanically-resolved bracket outcome directly from price history — no
live trade needed. Result: **50,000 rows, 42,772 resolved. Spearman IC(|score|, won) = -0.0024,
AUC(|score| → won) = 0.4986 — both at their null values, at 14x the statistical power floor.**
This is Part VI.1-R3, "the single most informative test," now actually run rather than blocked
on live trades — and it confirms, far more strongly than any live cycle could alone, that the
current blended score genuinely lacks discriminative power over this window. Long/short win
rates are close too (36%/35%), so it isn't a masked directional bias either. WARRANT#179 then
added a regime tag to the same export (reusing the live classifier) so a per-regime breakdown
(Part VI.1-R2) can check whether this pooled null hides real regime-conditional structure —
compiled, deployed, awaiting the next natural restart to produce the regime-tagged file.
**Consequence: further blind live restarts to re-confirm Phase 1's null result are now low
marginal value — the real next lever is the redesign/meta-labeling program, not more repeats.**

## What happened with the live run

**CORRECTION (2026-08-26): the instrument is USDJPY M5, not USDCHF H1.** Earlier entries in
this file said USDCHF — that was wrong, read off a multi-chart terminal's active/focused window
title rather than the actual per-line-tagged expert log (`MQL4\Logs\20260825.log` /
`20260826.log`, which is authoritative and says `USDJPY,M5` on every single line). Corrected
here; see `forge_ledger.json` pass_168 for the full honest note.

**TUNGSTEN completed TWO full calibration cycles overnight on the demo account (USDJPY M5) —
both firsts for this project** (no prior run had ever reached a terminal verdict without
truncating). Both ended **STAND DOWN / OVERFIT** (train ~28.6% → OOS 0.0%, 3/6 gates, zero
trades placed each time) — the safety system working correctly, not a malfunction.

**Real diagnostic finding acted on: Phase 3B's regime-level dir-check found "Strong Bear:
SIGNAL INVERTED" (forward 36% WR vs reverse 47% WR) in BOTH overnight runs, at n=6263 and
n=6329 — comfortably above the n≥500 real-trading-weight floor this project already requires
for any live trim.** That finding had existed in the code for a while but was diagnostic-only
("drives future architectural decisions" per its own comment) — never wired to anything.
**WARRANT#176 wires it**: a new bounded [0.70,1.0], reduce-only trim
(`ComputeRegimeInversionTrim`), same non-negotiable doctrine as the existing WARRANT#30 trim
(never flip a signal's direction, only reduce conviction), persisted across restarts via a new
guarded save/load tail. Compiled 0/0, deployed, and the terminal was restarted (closed +
relaunched — an already-attached EA does not hot-reload a new .ex4) specifically to test this
fix against a fresh calibration. **This is now the live loop**: fix → recalibrate → observe →
confirm or refute → fix again, per Manuel's explicit instruction, with a dead-end/stall watch
(CPU-flat + log-flat during expected active computation) added so a genuine hang gets caught
and reacted to, not just silently waited out.

**Consequence: because zero trades were placed either run, `TUNGSTEN_pathstate_export.csv` is
still empty.** The two completed-calibration milestones are real and valuable (prove the
pipeline finishes, prove stand-down logic holds under real repeated conditions) — but neither
feeds the research-layer tools by itself. `ARMED save skipped` both times, so the next launch
recalibrates fresh again — exactly what's now running with WARRANT#176 in place.

## What's built and tested (all self-tested against known-answer cases before shipping)

**MQL4 (compiled 0/0, marker-verified, byte-identical across all 3 deploy locations):**
- WARRANT#170 — path-state capture (MFE/MAE/duration/regime-drift per trade)
- WARRANT#171 — export bridge, `TUNGSTEN_pathstate_export.csv` (empty until a trade closes)

**Python — `research_layer\`:**
- `analyze_pathstate.py` — R1/R2/R3 reframe tests (expectancy-in-R, per-cell conditional
  expectancy, IC/AUC), power-floor-gated
- `afml_tools.py` — the full Part VIII.0 method list: triple-barrier labelling, average
  uniqueness, purged K-fold, combinatorial purged CV, deflated Sharpe ratio, PBO/CSCV, trend
  scanning, a first-cut meta-model wrapper, fractional differentiation. 9/9 self-tests pass.

**Python — `cerberus\`:**
- `cerberus.py` — 8 validation gates (G-REACH/G-POWER/G-STALE/G-STACK/G-SEED/G-TELE/G-SELF/
  G-COST) + `read_trial_count()`, each reproducing a real project incident as its own test. 9/9
  self-tests pass. G-SEED validated against the real TUNGSTEN source (correctly confirms
  `g_Risk.minRisk` now has real assignment sites, matching WARRANT#167).
- `run_cerberus.py` — the pipeline that produces `CERBERUS_VERDICT.json` (Part IV.7's named
  deliverable). Self-tests both modules before running; currently reports real trial count (163
  distinct warrants) and a real reducer-stack finding (see below), and honestly reports
  INSUFFICIENT_DATA for anything needing real trades.

**A real finding surfaced by running the pipeline, not just building it:** the current live
reducer stack's worst-case simultaneous-trigger product is exactly 0.0 (Kelly ceiling and
drawdown fade can each independently floor at 0.0) — below the 1.0% no-edge floor WARRANT#167
established. Safe (undershoot only), but real and now has a re-runnable check instead of a
one-time hand calculation (`python cerberus\run_cerberus.py`).

## What's genuinely not done, and why

- **Steps 6+ of the ship order need real closed-trade data.** None exists yet — the export CSV
  is empty. This is the one thing that requires elapsed real time, not more building.
- **CEA (Part VII, the continuous-exposure architecture) is not implemented in MQL4.**
  Deliberately not started while the live run is active (same reason as above — don't touch the
  source under a running calibration).
- **`purgedcv` was not installed.** Implemented the same algorithms directly from the published
  papers instead, rather than pip-installing an unfamiliar package unattended overnight.
- **G-SELF is a registry, not an enforcement mechanism** — it records which instruments are
  validated, it does not yet block an unvalidated one from being used automatically.

## To pick this back up

Say **"sword master tungsten"** — the skill at `~/.claude/skills/sword-master-tungsten/` re-reads
`SWORD_II_MASTER.md` and this file, checks `forge_ledger.json`'s real latest pass, checks whether
the live run produced anything (`TUNGSTEN_pathstate_export.csv`, `TUNGSTEN_live.log`), and
resumes from there — not from a stale memory of tonight.
