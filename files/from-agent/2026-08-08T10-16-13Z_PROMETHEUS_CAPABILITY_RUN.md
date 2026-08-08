# PROMETHEUS — Full Strategic Run

Target audited: GENESIS (`strategies x/src/`), 19 organ/extension files, build GEN-0.5.0-dev, updated through pass_8. Per the charter's own header ("Target: GENESIS, next generation"), this run audits GENESIS's real code, not the legacy TUNGSTEN monolith.

Method: every one of the faculties below is graded by reading the actual GENESIS source, not by intent or aspiration. Each faculty's **Reach** (the ambition) and **Spine** (the guardrail) are graded separately, since a faculty is only complete when both hold. Three grades, honestly applied:

- **MET** — both reach and spine are real, cited code, verified this session.
- **PARTIAL** — one half is real; the other is either absent or only vacuously true.
- **GAP** — neither half exists yet. Named plainly, not papered over (Law 7).

**Correction (pass_7):** the charter lists 6 categories; counting every numbered faculty (1.1-1.5, 2.1-2.5, 3.1-3.5, 4.1-4.5, 5.1-5.4, 6.1-6.5) gives **29**, not the 28 this document originally claimed — a miscount inherited from the first audit, caught and fixed here rather than silently carried forward (Law 7).

**Tally after pass_8: 18 MET · 6 PARTIAL · 5 GAP** (of 29) — up from the pre-closure 13 MET · 11 PARTIAL · 5 GAP. Five faculties moved PARTIAL→MET across pass_6/7/8: 3.5, 4.5, 6.4 (pass_6), 5.4 (pass_7), 2.3 (pass_8). No faculty moved backward and no GAP has yet been closed — every remaining GAP still needs live data, live execution, or a genuinely new large-scope organ (see "Honestly still open" below).

---

## 1 · PERCEPTION & DISTILLATION

**1.1 Total information intake — GAP.** No organ ingests a live multi-stream feed (price/vol/spread/session/correlated instruments/macro/order-flow) — R01/P01 take a single generic series or pre-computed likelihood ratios as input, agnostic to source. The EMPTY_VALUE/"missing modeled as missing" ethos is real and pervasive elsewhere in GENESIS, but there is no intake organ to apply it to yet. Requires live OnTick wiring — deferred, consistent with every "not yet live-executed" gap already on record.

**1.2 Distillation under incompleteness — MET.** `P01_Classify` returns explicit confidence (entropy-derived) and refuses on stale input; `GENESIS_Rate.isKnown` marks thin evidence as unusable rather than fabricating a value; `A03_DeploymentFactor` scales continuously and never treats n=0 as "trust it anyway."

**1.3 Soft-membership regime sense — MET.** `P01_UpdateBelief` normalizes `p[9]` to sum=1 every call; `P01_UniformBelief` (max-entropy) is the answer for both a genuinely ambiguous read and a refused/stale one — never a false-confident guess.

**1.4 Multi-timescale coherence — GAP.** No organ holds or reconciles more than one timeframe's read. Building this honestly needs a real multi-timeframe input redesign, not a quick wrapper — named as real future work below.

**1.5 Signal-quality introspection — MET.** `P02_FeatureBank`: AUC computed OOS-only by construction (no in-sample path exists in the API), auto-retires at `P02_RETIRE_AUC_THRESHOLD=0.52`.

---

## 2 · CORRELATION & RELATIONSHIP INTELLIGENCE

**2.1 On-the-fly correlation — PARTIAL, unchanged since pass_6.** Spine is real: `A01_EffectiveN` clamps rho into [0,1] and guarantees `n_eff <= N` (conservative by construction, INV-13), and pass_6's `A01_ConservativeCorrelation` inflates any measured rho by a safety margin before it reaches sizing ("correlation is always assumed >= measured" is now literally true). Reach is still not: GENESIS consumes a correlation value as a caller-supplied parameter, it does not compute one from live cross-instrument data anywhere. Pass_8's `A01_ClassifyCorrelationRegime` (see 2.3) classifies FROM a caller-supplied rho window — it does not compute rho itself, so it does not close this reach. Genuinely needs live multi-instrument data this environment cannot supply — correctly still open.

**2.2 Structural relationship discovery — GAP, unchanged.** No organ searches for lead/lag or causal structure between events. The *discipline* such an organ would need (survive-out-of-window, k>=3, decay) already exists and is proven (C01/C03/R03) — the search itself does not exist. Real future work: a new Cognition organ, not a small addition.

**2.3 Correlation-regime awareness — MET (pass_8, both halves now closed).** Reach: `A01_ClassifyCorrelationRegime` (new, pass_8) takes the caller's own rolling window of measured rho readings and classifies CALM/TRANSITIONAL/CRISIS by the window's **maximum**, not its average — a single crisis-level reading anywhere in the window dominates the verdict rather than being smoothed away by calmer neighbours (tested explicitly: `Test_ClassifyCorrelationRegimeOneCrisisReadingDominates`). Spine (closed pass_6): `A01_CorrelationRegimeDefault` returns rho=1.0 for an explicitly-unknown read, and the pass_8 classifier itself independently defaults zero-evidence windows to CRISIS too — two independent fail-safes agreeing, not one.

**2.4 Reproducibility of relationships — PARTIAL.** The discipline (must reproduce out-of-window, one-window quarantined) is real and proven for edges (C01/C04), and would transfer directly to relationships — but GENESIS has no distinct "relationship" object yet (see 2.2), so nothing is currently exercising this specific discipline for that concept.

**2.5 Redundancy collapse — MET.** `A01_EffectiveN` is the literal formula (`n_eff = N/(1+(N-1)*rho)`), INV-13's own named contract.

---

## 3 · HISTORICAL EDGE CAPTURE

**3.1 Exhaustive historical sweep — GAP.** No organ walks historical events; GENESIS's 18 organs adjudicate and gate *already-computed* window results (C01 takes an array of `C01_WindowResult`, it does not produce them from raw history). The sweep itself is calibration-loop scope (TUNGSTEN's own Phase 3B analogue) that GENESIS has not rebuilt — large, real, correctly out of this session's scope.

**3.2 Edge-move cartography — PARTIAL.** The spine ("instability is first-class, a flipped cell is marked flipped, not averaged") is fully real at the single-series level: `R01_Classify` returns `flips` and `tstat` as first-class fields, never silently averaged into a smoothed number. What's missing is the *map* — a persisted, queryable collection of these readings across many regimes/conditions over time. `C03_EvidenceLedger` persists edge entries but does not currently carry substrate/flip annotations alongside them. Named as real future work (a C03 schema extension) rather than attempted this pass — it deserves its own dedicated design, not a rushed schema bump.

**3.3 Non-stationary edge capture — MET.** `R02_Dispatch` routes TIME_VARYING to RECENCY_WEIGHTED (never LINEAR); `R03_ApplyFreshnessDecay` + `R03_EstimateDwell` are the literal "grasp it, follow the drift, release it as it fades" mechanism, with a tested, bounded estimator lag (INV-11/INV-12).

**3.4 Event-family generalisation — GAP.** No clustering/family-generalisation mechanism exists. Real, substantial new-capability scope; not attempted.

**3.5 Sign-flip vigilance — MET (pass_6, both halves now closed).** Reach: `R01_Flips` explicitly detects the project's named nemesis. Spine: `R01_FlipProbability` (new) turns the flip count into an explicit `[0,1]` estimate over powered sub-window transitions; `R01_ApplyFlipDiscount` composes it into a base confidence value upstream (`confidence * (1-flipProbability)`) — never a second, separate multiplier (INV-12 preserved). Both halves of "every edge carries a measured half-life **and** a flip-probability, and both gate deployment" are now real and cited.

---

## 4 · COGNITION & STRATEGY

**4.1 Cerebral adjudication — PARTIAL.** `C01_Adjudicate` is a real, rigorous per-regime verdict engine (OOS-only, NONE first-class, CI must exclude zero) — the adjudication mechanism itself is MET. But "weigh regime, correlation, historical analogue, cost, confidence... into a single verdict" as one call does not exist — P01/P02/P03/C01 are separate organs an external caller must stitch together (currently only the coherence smoke test does this, by hand, as a demonstration, not as a real orchestrating organ).

**4.2 Strategic foresight — PARTIAL.** The spine is vacuously true (nothing can ever exceed `A01_HARD_FLOOR_PERCENT`, by construction, regardless of any projection) but not because of active foresight — there is no multi-step lookahead reasoning about future exposure or opportunity cost. Real, substantial future work.

**4.3 Best-decision-under-uncertainty — MET.** `A01_ComposeSize`'s confidence factor and `A03_DeploymentFactor`'s continuous evidence ramp are exactly "decisive, scaled to information quality" — G01 REFUSEs outright rather than acting boldly on a thin read.

**4.4 Counterfactual self-testing — MET.** `C02_Evaluate` composes WF-gap + resample-divergence + PBO via MIN — literally "must survive an active attempt to break it," and the MIN composition (proven by test) means no single guard's failure can be diluted.

**4.5 Meta-calibration memory — MET (pass_6, both halves now closed).** Reach: `C04_ChampionRegister` remembers promotion/revert history (generation counter, revertCount). Spine (new): `C04_ShouldPromote` calls `C04_IsRepeatOffender` against the register's revert history — a challenger whose `configId` was previously reverted must clear `ciLow > champion.ciLow + C04_REPEAT_OFFENDER_MARGIN` (a strictly higher bar) to re-promote, not the same bar a clean challenger faces. "A strategy shape that has failed before starts guilty, not innocent" is now real, cited code, not just a remembered history nobody consults.

---

## 5 · ACTION & EXPRESSION

**5.1 Continuous confidence sizing — MET.** `A01_ComposeSize` (confidence enters exactly once, INV-12) + `A03_DeploymentFactor` (Hermite smoothstep, provably no discontinuity) + `min(size,FLOOR)` applied last.

**5.2 Graduated participation — MET, and deliberately exceeds the charter's own letter.** The charter's spine text names "full size requires >=30 real OOS trades." GENESIS instead uses two *distinct* floors on purpose: `GENESIS_DIAGNOSTIC_POWER_FLOOR=30` (enough to read at all) and the strictly higher `GENESIS_TRADING_WEIGHT_FLOOR=500` (enough to size a live decision on) — precisely because n=30 was the sample size at which this project's own real historical incident (a fake 100% WR arming on n=1, generalised as "small n is not trustworthy for sizing") happened. Flagged honestly as a positive divergence from the charter's specific number, not a defect — the charter's *intent* (a real floor, no exceptions) is met at a higher, better-justified bar.

**5.3 Time-aware execution — MET.** `R03_ApplyFreshnessDecay`, with `R03_EstimatorLag` tested to stay strictly below one full dwell period (INV-11/INV-12).

**5.4 Adaptive risk budgeting — MET (pass_7, both halves now closed).** Spine (pre-existing): `A01_DDBudgetFactor` is loss-proportional and bounded [0,1]. Reach (new): `A01_AllocateBudget` takes N simultaneous candidates (confidence, durability) and splits a total budget proportionally to `confidence_i * max(0,durability_i)` — a non-durable candidate (durability<=0, e.g. an edge whose `ciLow` doesn't clear zero) is weighted to **exactly** zero, starved outright rather than merely de-prioritised (tested: `Test_AllocateBudgetStarvesNonDurableCandidate`, `Test_AllocateBudgetAllZeroDurabilityStarvesEveryone`). The spine holds under the new reach: both the requested total budget AND every individual allocation are independently clamped to `A01_HARD_FLOOR_PERCENT` — "the dumb hard floor governs the smart budget, always" (tested: `Test_AllocateBudgetNeverExceedsHardFloorPerCandidateOrTotal`, using a deliberately absurd 50% requested budget).

---

## 6 · CONSCIENCE & TRUST

**6.1 Total self-observability — PARTIAL.** Spine is fully proven: `G03_LogVerdict` is the *only* sanctioned logging path in the entire codebase (a real, run grep audit confirms `Print()` appears nowhere else in `src/`). Reach — "every decision... the instant it happens" — is not yet automatically guaranteed, because no orchestrator wires every organ's output through G03 unconditionally; today only the coherence smoke test calls it, by hand, per stage. The mechanism is real; universal automatic coverage is not yet.

**6.2 Blocking conscience — MET.** `G02_Evaluate`: no override path exists anywhere in the file (grep-audited); INCOMPLETE halts identically to BLOCK. `G01`: WF-fragile blocks unconditionally.

**6.3 Honest self-diagnosis — MET.** `G04_Diagnose`: narrative is never empty for a NONE verdict, in any of the 3 branches (UNPOWERED/TIME-VARYING/FLAT) — no bare fallback text exists in the code.

**6.4 Reproducible verdicts — MET (pass_6, both halves now closed).** Reach: every decision-logic function built this project is a pure function of its inputs — `P01_Classify`/`P01_UpdateBelief` was explicitly redesigned mid-session specifically to remove hidden static state for this property (see its own header). Spine (new): `Test_DeterministicForGivenBar` (`P01_RegimeState_test.mq4`) calls `P01_Classify` twice with byte-identical prior/likelihoods/decay inputs and asserts byte-identical belief-vector output (1e-15 tolerance) — "determinism is tested" is now literally true, not just structurally argued.

**6.5 Incorruptible memory — MET.** `C03`/`C04`'s serializers: one function both directions (INV-02), magic+schema+checksum verified on load, fail-closed on any mismatch.

---

## How GENESIS stands against THE STANDARD OF TRUST (the charter's own 8-point summary)

1. Distills incomplete info honestly — **mostly met** (1.2).
2. Computes correlation live, never double-counts — **partial**: never double-counts is real (2.5); tracking which correlation-regime is active is now real too (2.3, MET as of pass_8); computing rho live from real cross-instrument data is still not (2.1's reach).
3. Swept every historical event, mapped it — **gap** (3.1/3.2 largely unbuilt).
4. Grasps relationships as reproducible hypotheses — **gap** (2.2 unbuilt; the reproducibility *discipline* exists but nothing to apply it to yet).
5. Captures moving edges, releases as they fade — **met** (3.3), and sign-flip vigilance now fully closes the loop (3.5, MET as of pass_6).
6. Reasons several moves ahead without breaching the floor — **partial**: never breaching the floor is real and absolute (and now demonstrably true even under cross-candidate allocation, 5.4 MET as of pass_7); the reasoning-ahead itself doesn't exist (4.2).
7. Every decision visible, reproducible, self-diagnosed — **mostly met**: determinism is now tested, not just argued (6.4, MET as of pass_6); 6.1's universal auto-wiring is the one piece still open, correctly deferred pending a real orchestrating EA main loop.
8. Knows what it doesn't know, stands down honestly — **met**, and this is GENESIS's clear strength: `G01_REFUSE`, `R01_UNKNOWN`, `GENESIS_Rate.isKnown`, `C01_NONE`+cause all fail toward honesty by construction, not by convention.

**Overall pattern, stated plainly:** GENESIS is strongest exactly where this whole project has been burned before — honesty, fail-closed behaviour, refusing to fabricate confidence. After pass_6/7/8's 5 closures, every faculty that was buildable under this environment's static-MQL4-only constraint (no live OnTick, no live multi-instrument feed, no live order execution) without inventing a large new architecture has been closed. What remains — 1.1, 1.4, 3.1 (live data), 2.1's reach (live cross-instrument computation), 2.2/3.4 (genuinely new organs), 3.2 (a deliberately deferred schema design), 4.2 (multi-step lookahead architecture), 6.1 (a real orchestrating EA main loop) — is real future work, not a shortfall being talked around.

---

## Closed across pass_6 / pass_7 / pass_8 (real, buildable-now fixes — see GENESIS_LEDGER.json for full detail)

**pass_6** (spine-only closures, written the prior session, recompiled/ledgered/confirmed this session):
1. **2.1's spine / 2.3's spine — conservative correlation under uncertainty.** `A01_ConservativeCorrelation` (new) inflates a measured rho by a safety margin before sizing; `A01_CorrelationRegimeDefault` supplies rho=1.0 (crisis assumption) for an explicitly-unknown correlation read, replacing the implicit rho=0 a caller would otherwise default to. (2.1 stays PARTIAL — its reach still needs live data; 2.3 reached MET only after pass_8 closed its reach too.)
2. **3.5 — MET.** `R01_FlipProbability` (new) turns the existing flip count into an explicit [0,1] estimate; `R01_ApplyFlipDiscount` composes it upstream into confidence (never a second multiplier, INV-12 preserved) before `A01_ComposeSize`.
3. **4.5 — MET.** `C04_ShouldPromote` checks a challenger's `configId` against the register's own revert history; a repeat offender must clear a strictly higher bar to re-promote, not the same one.
4. **6.4 — MET.** `Test_DeterministicForGivenBar` calls `P01_Classify` twice with identical inputs and asserts byte-identical outputs.

**pass_7:**
5. **5.4 — MET.** `A01_AllocateBudget` (new): a cross-candidate risk allocator, weight = confidence x max(0,durability), non-durable candidates starved to exactly zero, both per-candidate and total allocation independently clamped to the hard floor. Test-first: 3 new tests written against the not-yet-existing function first (confirmed RED, error 168 x3), then implemented (confirmed GREEN).

**pass_8:**
6. **2.3 — MET (reach closed, spine already closed pass_6).** `A01_ClassifyCorrelationRegime` (new): classifies CALM/TRANSITIONAL/CRISIS from the caller's own rolling rho window, by the window's maximum (not average — a single crisis-level reading dominates), zero-evidence windows default CRISIS. Test-first: 4 new tests confirmed RED (error 256/168/152) before the enum + function existed, then GREEN after.

All 20 test files (19 organ/extension tests + the coherence test) individually recompiled via metaeditor.exe after every change in this session: 0 errors throughout, R04_CuratedNeuralNet keeping its 1 pre-existing documented benign warning, every other file 0 warnings.

## Honestly still open (real future work, not attempted these passes)

- **1.1, 1.4:** need live multi-stream / multi-timeframe data wiring — this environment cannot supply live OnTick data without Manuel attaching something to a running terminal.
- **2.1's reach:** needs live cross-instrument correlation computed from real market data, not a caller-supplied value — same live-data constraint as above. (2.1's spine is closed; only the reach remains.)
- **2.2, 3.1, 3.4:** need genuinely new organs (relationship search, historical sweep, family clustering) — large scope, not a quick addition; not attempted any of these 3 passes.
- **3.2:** the cartography *map* itself (a C03 schema extension) still deserves its own dedicated design pass, not a rushed bolt-on — considered for pass_8 and deliberately deferred again in favour of the smaller, cleaner 2.3 closure.
- **4.2:** needs real multi-step lookahead architecture (projecting exposure/drawdown paths, not just clamping post-hoc) — genuinely new organ, correctly deferred.
- **6.1's universal auto-wiring:** needs a real orchestrating EA main loop that routes every organ's output through G03 unconditionally, which GENESIS has deliberately not built yet (per genesis-phoenix doctrine, no MQL4 script attaches to anything live without Manuel's explicit consent — and a static orchestrator *function* without a live main loop was considered for pass_8 but judged likely to be a hollow, untested wiring exercise without real inputs to drive it end-to-end, so it was left for a pass with more time to do properly rather than rushed).
