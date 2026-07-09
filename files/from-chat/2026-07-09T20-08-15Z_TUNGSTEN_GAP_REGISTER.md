# TUNGSTEN — THE GAP REGISTER
### Design intent vs. the truth of what is implemented, with strategic bridges
Authored from a direct read of TUNGSTEN 9.44 SLS(30), 55,222 lines.
Companion to the tungsten-forge Pass 3 directive.

---

## HOW TO READ THIS

Each gap is stated as three lines:
- **INTENT** — what the architecture's own comments/structure say it is *supposed* to do.
- **REALITY** — what the code, read literally, *actually* does.
- **BRIDGE** — the strategic change that closes the distance, with the mechanism, not a slogan.

Gaps are ordered by leverage. G1 is the root cause of the STAND DOWN; fixing it changes the
verdict. The rest compound.

---

## G1 — THE SINGLE-SPLIT GAP  *(root cause of the overfit STAND DOWN)*

**INTENT.** *"TRAINING SPLIT: 70% for optimization, 30% for holdout validation."* (line 6378).
The design is honest cross-validation: learn on data you have seen, prove on data you have not.

**REALITY.** There is **one** split. `TRAIN_START` is a single fixed boundary (line 34261). Every
optimizer — IC weights, session weights (`sCnt*0.7`, line 5988), volatility weights, TP/SL —
selects the best-fitting parameters on the *same* 70% and is then checked *once* on the *same*
30%. The overfit-check fires **after** selection has already happened on the training portion.
So the system does exactly what a single split guarantees: it finds the parameter set that best
fits one arbitrary slice of history, then acts surprised when the other slice disagrees. All nine
regimes showed the identical −19 to −44pp collapse **because they share this one mechanism** — it
was never nine independent non-findings, it was one structural flaw expressed nine times.

**Why this is fatal at scale:** Phase 3B searched 562,500 combinations against this one split.
The mathematics is unforgiving — the *luckiest pure-noise combination* out of 562,500, at n=1000,
shows **+0.188R of "edge" by chance alone.** That number is not a coincidence; it is the −19-to-44pp
holdout collapse, viewed from the other side.

**BRIDGE — walk-forward replication (Pass 3 W#10).**
Replace the single split with **3–5 disjoint, chronological windows.** A parameter set is accepted
**only if it beats the equal-weight baseline on the orthogonal metric in a majority of windows AND
its out-of-window mean is positive.** Add a selection penalty sized to the search count: the
acceptance bar rises with `log(combos)`, so a 562,500-combo search must clear the ~0.188R noise
ceiling before any "winner" is believed.

The leverage is exact and provable: a pure-noise combination survives one window by chance with
p=0.50 (a coin flip — the current filter is *worthless*). It survives **five** windows with
p=0.031 — **32× harder to fool.** A real relationship replicates across windows; a fitted one dies
in the second. This single change converts "more testing" from a liability into an asset.

---

## G2 — THE MARGINALS GAP  *(the system cannot see relationships, only voices)*

**INTENT.** Manuel's stated goal: *"learn correlations and relationships with all the information
at hand regardless of market complexity… cause and effect pattern of complexity the whole lot."*
The design aspires to understand how signals *combine* and *lead* one another.

**REALITY.** TUNGSTEN measures **single-voice IC per regime only** — the marginal correlation of
each of six components with forward outcome, in isolation. Verified by direct search:
**pairwise/interaction correlation: essentially absent. Lagged/transition-conditioned edge: zero
occurrences.** The system has no machinery to ask *"does momentum + structure predict together
when neither does alone?"* or *"does Building Momentum at bar t forecast Strong Bull profitability
at t+k?"* It sees a list of voices, never the conversation between them. **This is the single
largest gap between the design's ambition and its reality.**

**BRIDGE — the relationship layer (Pass 3 W#11, W#12).**
Add three new classes of measurement, each powered (n≥500), each null-controlled, each required to
replicate across the G1 walk-forward windows before it is stored:
1. **Pairwise interaction IC** — the joint predictive power of component pairs, reported against
   the *sum of their marginals* (interaction only counts if the pair beats its parts).
2. **Lagged cross-regime edge** — regime at bar `t` conditioning profitability at `t+k`. This is
   the literal "cause and effect" the design names, and TUNGSTEN already computes a regime
   transition matrix — the raw material exists; the edge-conditioning does not.
3. **Cross-session / cross-HTF conditioning** — collapsed until each cell reaches n≥500.

Every surviving relationship is written to a provenance table in `forge_ledger.json` (pair/lag/
regime, IC, n, windows-survived, null-subtracted effect), so the system *accumulates* a map of
what actually relates to what — the compounding intelligence, made durable.

---

## G3 — THE POWER GAP  *(partially bridged in SLS(30); must be proven, then extended)*

**INTENT.** Learn a weight per regime from that regime's evidence.

**REALITY, pre-SLS(30).** The IC pipeline gated only on `n < 30`. But with forward-R noise at
σ=1.28, a cell needs **n≥500 even to detect a 0.20R edge, and n≥1,000 to see 0.14R.** Regimes 4 and
8 calibrated on **140 and 150 trades** — an MDE of ~0.37R, meaning they could only detect an edge
so large no strategy possesses it, and were otherwise weighting pure noise. This is *the mechanism*
of the overfit at the cell level.

**REALITY, SLS(30).** W#9 raised the floor to `n < 500` at both IC sites. **Verified present in the
build** — but its effect is still `PENDING_BACKTEST`: no live calibration has yet confirmed that
regimes 3/4/8 now retain priors instead of overfitting.

**BRIDGE.** (a) Confirm W#9 on a real calibration run. (b) Extend the doctrine everywhere a number
is learned — session weights still admit at `sHoldout < 10` (line 5991), volatility weights
similarly. Every learning cell must report its **MDE** and return the prior when under-powered.
(c) The relationship layer (G2) inherits the same floor — a pairwise IC on 200 joint samples is
noise wearing a costume.

---

## G4 — THE PARITY GAP  *(calibration may be validating a system that will not trade)*

**INTENT.** The ghost simulates the live system, so its verdict means something.

**REALITY.** Historically, logic existed in **two copies** that drifted — the regime-8 hard gate
and its soft-score mirror used *different constants for the same question* (found and fixed in the
Claude passes). The structural risk remains wherever scoring, TP/SL, sizing, or a gate is computed
in more than one place: **the ghost may be validating a system the live path does not run.** This
gate has **never been verified for real.**

**BRIDGE — the Parity Invariant (Pass 3, Stage 6 hard gate).**
Calibration, ghost, and live must invoke **the same function** — not an equivalent one — for every
decision. Enforce a single `ComputeEntryDecision(context)` entry point where context affects only
data source, never thresholds or geometry. **Prove it:** replay the last 500 live bars through the
ghost path; every decision must match bar-for-bar. A mismatch is P0 and halts the pass. Until this
passes, no ghost verdict — pass *or* fail — is fully trustworthy.

---

## G5 — THE AUDITOR GAP  *(nothing has ever checked that the ghost tells the truth)*

**INTENT.** The ghost gate is the final arbiter of whether TUNGSTEN may trade.

**REALITY.** The arbiter itself is **unaudited.** Nothing verifies that the ghost reports ≈0 when
there is genuinely nothing to find. If an intrabar TP/SL resolution bias, a geometry error, or a
look-ahead leak gives the ghost a phantom edge, then *every verdict it has ever produced is void* —
including the STAND DOWN, which might be masking a deeper problem or a real edge.

**BRIDGE — the Null-Ghost (Pass 3, Stage 6 hard gate).**
Run the complete ghost pipeline on two surrogates built from the instrument's own bars:
**phase-destroyed** (permuted returns) and **sign-flipped**. Both must return `meanR ≈ 0, p > 0.01`.
*Verified feasible on the reference data:* +0.0325 (p=0.121) and −0.0318 (p=0.125) — both PASS, and
the residual **±0.03R at n≈3,800 is the apparatus noise floor**, now a permanent humility constant:
any measured `|meanR|` below it, at that n, is uninterpretable. If the ghost profits from shuffled
noise, it is broken — halt, and void every downstream number.

---

## G6 — THE VESTIGIAL-PHASE GAP  *(declared capability that does not run as designed)*

**INTENT.** Phase 3B.5 (session weights), 3B.6 (volatility weights), 3C.5 (session TP/SL) are
described as full refinement phases producing per-context intelligence.

**REALITY.** Their history is a graveyard of the exact failures this whole effort exists to end:
3B.5 was a 117,649-combo synchronous grid that **froze the terminal**, reverted to a no-op, then
rebuilt as time-budgeted coordinate descent. These phases *run* now, but they inherit **G1 (single
split)** and **G3 (thin cells)** — so they are producing exactly the kind of per-context weights
most prone to overfit, on the least data. A session×regime cell is far thinner than a regime cell.

**BRIDGE.** Subordinate every sub-phase to the G1 walk-forward and G3 power floor **before**
trusting its output. A session×regime weight that cannot clear n≥500 across a majority of windows
must return the parent regime weight, logged as `UNDERPOWERED` — not a fabricated refinement. Better
to inherit a proven coarse weight than to invent a fine one from noise.

---

## THE STRATEGIC ORDER OF REPAIR

The gaps are not independent; they must be bridged in dependency order:

```
G1 (walk-forward)  ─┬─►  makes G2 (relationships) trustworthy — a relationship
                    │     is only real if it replicates across windows
                    ├─►  makes G6 (sub-phases) safe — they inherit the discipline
                    │
G3 (power floor)  ──┴─►  gates every cell in G1, G2, G6 — no under-powered
                          learning anywhere
G4 (parity)  ───────────►  must pass before any ghost verdict is believed
G5 (null-ghost)  ──────►  must pass before the ghost is trusted to arbitrate
```

**G1 and G3 are the load-bearing bridges.** Together they turn the system's ambition — *learn every
relationship regardless of complexity* — from a route to overfitting into a route to genuine,
replicated knowledge. G2 is what the owner actually asked for; it is only *safe* to build once G1
and G3 hold. G4 and G5 are the gates that make the eventual verdict mean something.

---

## THE ONE-SENTENCE GAP

> **TUNGSTEN was designed to learn what genuinely predicts profit and to prove it on unseen data;
> what it actually does is find what best fits one slice of the past, measure each signal in
> isolation, and check itself once — so it mistakes the luckiest fit for the truest signal, and
> cannot see the relationships between signals at all.**

Bridging that sentence — replication instead of single-fit, relationships instead of marginals,
power-honesty instead of noise-weighting, and audited gates instead of trusted ones — is the whole
of the work that remains. It is not a rewrite. It is the disciplined completion of the design that
was always intended.
