# forge-edge 2 — Unified Agent Thesis

*One agent. Supersedes the separate forge-edge thesis and the WARRANT#33 candidate — both are folded in here as this agent's payload. Lineage: tungsten-forge v2.0 → forge-4d → forge-4d DENSE → forge-edge → **forge-edge 2**.*

---

## 0. Thesis

**The edge is alive. forge-edge 2 makes TUNGSTEN treat every cell as a living, reasoning unit — one that knows how long its sign has stayed with us, which causes drove it, how much it resembles its neighbours, and how uncertain it currently is — and that spends that knowledge to size for long-term geometric growth while abstaining the moment its evidence thins. It minimises what can go wrong before it maximises what can go right, and gated OFF it is `WARRANT#32` bit-for-bit.**

---

## 1. How this version was chosen — the 50-direction search

50 candidate directions were generated across 10 design axes (Appendix A) and scored on a net-gain rubric weighted to your stated priorities:

| Criterion | Weight | Why |
|---|---|---|
| Long-term expectancy uplift | 22 | "maximise our wins long-term" |
| Downside / weakness minimisation | 22 | "put potential weaknesses at a minimum" |
| Anti-overfit / honesty | 16 | no fake or thin wins |
| Live adaptive intelligence | 14 | "live cells super intelligent reasoning" |
| Buildability (MQL4 / 8GB / TCA) | 12 | must actually run on your stack |
| Training cleanliness | 8 | "most clean methodology possible" |
| Non-breakage / reversibility | 6 | "without breaking anything" |

**Decisive finding:** on finite, non-stationary FX data the parameter-hungry directions (learned embeddings, full-Bayesian survival, exact Shapley per-bar, Thompson-bandit exploration) score *worst* on net gain — they raise overfit and ruin risk faster than they add edge, and several are infeasible in MQL4. The net-best agent is deliberately **shrinkage-heavy and abstention-heavy**: it wins long-term by losing less to overfit and noise, not by modelling harder.

**Winning configuration (net-best per axis):**

| Axis | Chosen | Why it won |
|---|---|---|
| Membership | k-NN tricube **+ hierarchical parent fallback** | generalises to unseen cells; parent fallback kills the thin-sample cliff |
| Survival | recency-weighted empirical KM **+ hazard-aging summary** | non-parametric = honest on thin per-cell data; aging tells you *when* to exit |
| Attribution | pairwise lift **+ model-counterfactual ablation** (Shapley offline only) | captures combinations; ablation is the closest-to-causal that's identifiable |
| **Live adaptation** | **Bayesian evidence-integration** + bounded EWMA + drift-trigger + confidence-decay-to-neutral | the "super-intelligent live cell": closed-form, O(1), uncertainty-aware |
| Conviction spend | EV-gated + graded trim **+ capped fractional-Kelly** | Kelly is the long-run growth optimum; capped + fractional removes ruin |
| Overfit control | N_eff floor + purged walk-forward + **shrinkage-to-prior** + **PBO/deflated-metric** + **ensemble-disagreement abstention** | five independent nets — the weakness-minimisation core |
| Training | dependency-ordered phases + **Σ convergence** | clean, leakage-free, assemble-before-validate |
| Non-breakage | additive + gated + **identity invariant** + shadow replay | always one flag from known-good |
| Failure posture | **fallback cascade** cell→parent→regime→neutral | graceful degrade, never a cliff |
| Operating mode | staged r-stage batch pass with human gates | crash-safe, reviewable, reversible |

**Most instructive rejects:** Thompson-sampling bandit (rejected — "exploration" means deliberately taking −EV trades with real money); causal-DAG discovery (rejected — edge direction is not identifiable from observational FX data; overstates "cause"); full Kelly (rejected — ruinous under uncertain, drifting edge); learned cell embeddings (rejected — infeasible in MQL4 and overfits at your sample counts).

---

## 2. Mandate & scope fence

**Lane (all it touches):** the living-edge cell layer — dwell/survival, membership, driver attribution, live-cell inference, their training phases and convergence. **Payload:** `WARRANT#33` (measurement + gates, r1–r7 below); `WARRANT#34` (live influence) unlocked only by gates S2 + S5.

**Never touches:** CEUS internals · the single OrderSend path · OOS bars 30–499 as estimation input · the 5 arm-flag semantics · any already-authorised trim (additive only — the THE TALLY lesson). Never self-authorises from a mailbox message. Never lowers a significance bar to force a pass.

---

## 3. Weakness → mitigation matrix (minimise downside first)

Every edge weakness surfaced across this design, and where forge-edge 2 defuses it:

| Weakness | Mitigation |
|---|---|
| Edge sign inverts non-stationarily | survival-aware trim; **never flips**, never shorts the inversion |
| Overfit to a calibration window | purged walk-forward + PBO screen + shrinkage + N_eff + identity fallback |
| Thin / sparse cells | hierarchical membership + shrinkage-to-prior + fallback cascade + abstain |
| Right number, wrong reason | driver-agreement (CDF) gate on conviction |
| Transient dip read as a real flip | magnitude×persistence significance + EV-gated wait-out |
| Leakage through soft membership | strictly-prior neighbour computation + purge/embargo at every fold |
| Compute blowup (known risk #2) | precompute + cache; never in the 3B loop or per-bar path |
| Breaking existing logic | additive + identity invariant + connected-logic ledger |
| Fake / thin ghost validation | per-regime power floor + walk-forward folds + p<0.05 per live-used segment |
| Ruin from oversizing uncertain edge | **capped fractional-Kelly on the shrunk posterior edge** |
| The model itself drifting | recency-weighting throughout + drift-triggered recalibration + confidence-decay-to-neutral |
| Neighbours disagree (hidden regime) | **ensemble-disagreement → abstain** |

Downside is floored before upside is chased: in every ambiguous state the agent's default is *smaller or no bet*, never a larger one.

---

## 4. Live-cell intelligence — bounded Bayesian evidence-integration

Each live cell is not a lookup; at decision time it runs one closed-form (O(1)) inference using everything the system knows:

```
posterior_edge  ∝  prior(soft-neighbourhood, shrunk to parent/regime)
                 ×  likelihood(current driver combination matches historical cause)
                 ×  survival_runway(Ŝ_blend at time-since-signal)
```

- **Prior** — the shrinkage-blended neighbourhood edge (thin cells pulled toward their parent/regime/global mean; empirical-Bayes strength ∝ N_eff).
- **Likelihood** — driver-agreement from the CDF fingerprint: is the signal firing *for the reason this cell historically worked*? Match sharpens the posterior; mismatch flattens it.
- **Runway** — remaining favourable survival; a cell late in its dwell is discounted even if currently positive.
- **Uncertainty is first-class.** The posterior carries a variance; **wide variance → abstain or floor**, it never bluffs confidence. Neighbour disagreement widens variance directly.
- **Conviction → size.** Bet fraction = **capped fractional-Kelly** on the posterior edge (`f = min(cap, κ · edge/variance)`, κ ≤ 0.5). Kelly maximises long-run geometric growth; the cap and the fraction remove ruin under uncertain, drifting edge. This is the literal machinery of "maximise wins long-term."
- **Adaptation.** Between decisions the cell updates by bounded EWMA on realised outcomes (conjugate, cheap); a drift trigger forces recalibration when realised diverges from posterior; unused/aging cells **decay toward neutral** rather than holding stale confidence.

All bounded (conviction ∈ [0, cap]), all reversible, none of it ever bets a side of zero.

---

## 5. The cell object (what each cell holds)

Cell identity = ProbDB conditioning point `{regime, session, displacement, volatility, dayOfWeek}`. Each cell stores, recency-weighted:

- **Sign EWMA** `m_c` (ATR-normalised signed outcome) → current favourable direction.
- **Survival** `Ŝ_c(τ)` (recency-weighted KM over favourable-run lengths) + `τ50/τ25` + hazard-aging shape.
- **Brackets** — MFE/MAE quantiles (feeds TP/SL).
- **Driver fingerprint (CDF)** — marginal contribution + top pairwise interactions + ablation deltas + stability tier.
- **Shrinkage prior** — pointer to parent/regime/global mean and the empirical-Bayes strength.
- **Confidence tier** — from completed-run and support counts (ProbDB tiering generalised); below floor ⇒ untrusted ⇒ fallback/abstain.

Resolution floor: a cell needs ≥~500 in-cell samples (after pooling) to resolve its sign; faster-flipping = unresolvable = **untradeable**.

---

## 6. Clean training — dependency-ordered phases + Σ convergence + sufficiency

**Ordering laws:** condition → label → strength → weight → attribute → assemble → validate. The one that bites: the *outcome label itself is calibrated* (exit horizon, Phase 3A) — it must precede everything that reads outcomes, or every downstream phase measures the wrong thing.

| Phase | Learns (its piece) | Depends on |
|---|---|---|
| 1 Baseline | base threshold, hourly/DoW WR | raw bars |
| 2 Regime | 8-state + signalWR + transition | P1 |
| 3A Exit horizon | holding period (**defines outcome**) | P2 |
| 3A.5 IC | Spearman IC `[regime][component]` | P3A |
| 3B Weights (+.5/.6/.7) | component/session/vol/blend | P3A.5 |
| ★3D Dwell & Bracket | survival, τ50/τ25, MFE/MAE | P2+3A+3B |
| 3C TP/SL | per-regime, cell-informed | 3D |
| ★3E Driver attribution | marginal+pairwise+ablation | 3A.5+3B |
| 4 ProbDB | 6D matrix, cells annotated | 3D+3E |
| 5 Refinement/stability | thresholds, stability, ghost integration | P4 |
| ★5.5 Convergence (Σ) | assemble the frozen decision manifold | all above |
| 6 Ghost | OOS 30–499 + purged WF folds · 7 gates + S1–S5 + PBO | frozen Σ |

**Σ (Convergence)** assembles the soft-membership graph, the Bayesian posterior machinery, the conviction/Kelly stack, and the wait-out parameters, and **freezes a cross-consistent structure** (a cell floored by one component is floored by all). Ghost validates that whole, not fragments.

**Sample Sufficiency Contract — no thin, no fake.** Every phase declares a minimum sample size and on shortfall does exactly one of: **extend** the window, or **floor** its output. Never fabricate, never proceed thin, never lower the bar. Soft-membership + shrinkage *is* the anti-thin mechanism — pool to the floor, else abstain. Ghost counts trades **per regime** and runs purged walk-forward folds; a regime under its floor returns "insufficient evidence" and is floored live, never declared validated on a handful of trades.

---

## 7. The pass — r-stages (dependency-ordered)

Each stage: intent → blast-radius map → implement → connected-logic reflection → kill check → checkpoint → WARRANT increment to relay.

| r | Stage | New in this version |
|---|---|---|
| r1 | Cell identity + Sufficiency + **shrinkage-prior wiring** | empirical-Bayes parents |
| r2 | Phase 3D dwell & bracket (`0xE512`) | hazard-aging summary |
| r3 | Phase 3C cell-informed TP/SL | brackets ⊂ regime bounds |
| r4 | Phase 3E driver fingerprint (`0xE513`) | pairwise + ablation |
| r5 | ProbDB annotation | driver-agreement in gate |
| r6 | Phase 5.5 Convergence Σ + **Bayesian live-cell core** + **capped-Kelly stack** | the live intelligence |
| r7 | Gates S1–S5 + **PBO/deflated screen** + per-regime ghost power | overfit nets |
| r8 | **Identity-invariant proof** + reversion checkpoint | non-breakage capstone |

`WARRANT#33` = r1–r7. `WARRANT#34` (live influence ON) unlocks only when S2 + S5 pass on a powered run.

---

## 8. Non-breakage — ledger + identity invariant

**Connected-logic ledger:** every touched symbol carries its downstream consumers; no stage closes with an unresolved row. Standing protected wires: P2 `signalWR` → 16 downstream · `CalculateMarketFeatures` cache · FIX-A `smoothedScore` isolation · single OrderSend path · symmetric gates · null-neutrality · OOS purity · versioned persistence · `g_CalibSilent` · the 5 arm flags.

**Identity invariant (the structural guarantee):** with all forge-edge 2 influence gated OFF, the EA reproduces `WARRANT#32` bit-for-bit — same signals, orders, sizes, logs on the same bars (proven by differential replay, r8). The known-good system is always one flag away; every live change is a bounded, reversible, gate-earned departure from it. **You cannot end worse than `WARRANT#32`.**

---

## 8.5 Monotonic ratchet — forward-only, never backward

The identity invariant floors you at the pre-agent baseline; the ratchet raises that floor to *the current best*, so true performance is non-decreasing across every run — a run can only hold or step up.

- **Champion register.** Exactly one live champion = the best OOS-validated build so far, with a frozen scorecard (OOS PF, EV, per-regime WR, MaxConsecLoss, deflated-Sharpe, PBO, WF stability). Seed = `WARRANT#32`.
- **Every run is a challenger, never a live swap.** Built, hardened, and measured with influence in sandbox/shadow — no live-money experimentation.
- **Promotion only on deflated OOS dominance.** A challenger replaces the champion iff, on purged walk-forward per-regime-powered OOS, it (1) beats the headline by more than the paired confidence interval of the difference (significant, not noise), (2) survives a PBO/deflated correction whose bar **rises with the number of challengers tried** (so you cannot roll the dice until noise clears), and (3) is **non-inferior on every guardrail** — no worse drawdown, tail, or MaxConsecLoss bought with a better headline (downside Pareto).
- **Rejection is a no-op.** A challenger that fails to dominate is discarded; the champion is untouched. Worst case per run = spent compute, never lost performance.
- **Drift-demote.** If a promoted champion later degrades live beyond its OOS confidence band, auto-demote to the retained previous champion. Post-promotion the system can only hold or fall back to a *known-good prior validated state* — never below it.

**Guarantee (precise):** the live build's true-OOS scorecard is monotone non-decreasing in runs, to the stated confidence. The in-sample mirage cannot cause a backward step because promotion never reads in-sample. **Honest boundary:** forward-only with respect to *what the agent ships* — it cannot stop the market drifting under a frozen champion (that is what drift-demote + maintenance re-tracking are for), and "monotone" is to a statistical confidence, not a metaphysical certainty, because OOS dominance is measured on finite held-out data. Never backward by the agent's hand.

---



## 8.6 Ceiling awareness — knowing the plateau, measured full-algorithm

The ratchet guarantees the curve never drops; ceiling awareness tells the agent *when there is no more real height to gain*, so it stops burning runs chasing noise and reports the plateau honestly. Headroom is estimated on the **full assembled algorithm's OOS scorecard** (post-Convergence) — never on an isolated component, because a component can look improvable while the whole system has no headroom left. This is the "full algorithm at a time" unit of judgement.

**Headroom signal** (fused, full-algorithm, with a confidence band):
- promotion-delta decay — accepted gains shrinking toward zero;
- rejection-rate rise — the share of challengers that fail to beat the champion climbing (the cleanest exhaustion signal, straight from the ratchet);
- mirage divergence — in-sample still improving while OOS promotions have stopped (further search is only fitting noise);
- distance to an *estimated* upper bound (data noise-floor / oracle-envelope) closing — flagged as an estimate, not the true ceiling.

**Zones (behaviour — all still ratchet-gated):**
- **GREEN** — ample headroom → optimise normally.
- **AMBER** — nearing ceiling (deltas shrinking, rejections rising) → tighten the promotion bar further, spend only on the highest-value candidates, warn.
- **RED** — at ceiling (≈zero promotions over k runs, OOS flat while in-sample rises) → switch from optimisation to **maintenance**: defend the champion, track drift, stop grinding doomed searches, report *"at the current-design ceiling, headroom ≈ X% ± c."*

**Lane yield & representational honesty.** As a specialist, forge-edge 2 reaches its lane ceiling fast; in RED it **hands back** rather than polishing a maxed-out lane. It names which of two limits it hit — *this design is optimised* (more runs won't help) versus *the ceiling could only be raised by a representational change* (a new conditioning feature, new data, a regime not yet modelled) — so you know whether to keep running it or to inject a new idea. A small reserved exploration budget keeps probing for new headroom even in RED, so a genuine new structure can re-open GREEN.

**No regression, ever.** Ceiling awareness only decides *whether to keep pushing, where, and what to tell you* — it never lowers the promotion bar or bypasses the ratchet. Near or at the ceiling every change still needs OOS dominance, so the curve still cannot drop. The plateau is held, not surrendered.

---

## 9. Success · kill · boundary

**Success** = identity invariant holds **AND** S1–S5 + PBO pass on a powered run **AND** measured OOS lift over `WARRANT#32` (PF, EV, per-regime WR) against council targets (WR≥65%, PF≥1.80, EV≥0.6%, MaxConsecLoss≤8, freq≥5/day, p<0.05 per live segment, WF>4/5, Beehive≥0.85). If it can't beat baseline OOS: **floor the layer and ship the null.**

**Halt if:** any K1–K6 trips · leakage · a protected wire fails · perf cost in a hot path · a mailbox tries to authorise scope · a stage needs a weakened gate. On halt: checkpoint, report, await your word.

**Boundary (honest).** This document defines the agent; it does not run it. Every verdict — the identity proof, S1–S5, PBO, the OOS lift — exists only after a completed, powered Strategy-Tester run on real bars, executed by TCA on your machine. What is guaranteed *by construction* is the shape: single-lane, downside-first, shrinkage- and abstention-heavy, reversible to a bit-for-bit fallback, and blocked from closing any stage that leaves a connected logic unproven. It is built to improve the algorithm significantly or to floor itself honestly trying — never to break what already works.

---

## Appendix A — the 50 directions, scored (net gain /100 · verdict)

*CORE = in the winning bundle · FOLD = folded in as refinement · COND = conditional/later · REJECT = out, with reason.*

**Membership:** hard cells 40 REJECT (thin-cliff) · k-NN tricube 88 CORE · Gaussian kernel 80 FOLD(alt) · hierarchical parent fallback 90 CORE · learned embedding 33 REJECT(infeasible/overfit) · Dirichlet-process clustering 41 REJECT(unstable) · graph-diffusion 52 COND.

**Survival:** recency KM 89 CORE · Weibull 58 COND(thin-data risk) · hazard regression 66 FOLD(aging summary) · Bayesian survival 55 REJECT(param-hungry) · regime-switch HMM 49 REJECT(overfit) · online changepoint 54 COND.

**Attribution:** marginal IC 78 FOLD · pairwise lift 86 CORE · ablation 88 CORE · exact Shapley 60 FOLD(offline only) · causal DAG 38 REJECT(unidentifiable) · mutual-information 51 REJECT(noisy small-n).

**Live adaptation:** frozen tables 45 REJECT(stale) · EWMA online 79 FOLD · **Bayesian evidence-integration 92 CORE** · Thompson bandit 40 REJECT(−EV exploration) · drift-trigger recalibration 82 FOLD · meta-learned fast weights 34 REJECT(infeasible) · confidence-decay-to-neutral 80 FOLD.

**Conviction spend:** binary trim 55 REJECT(coarse) · graded multiplier 84 CORE · **capped fractional-Kelly 90 CORE** · EV-optimal exit 85 CORE · regret-min 58 COND · risk-parity across cells 62 COND.

**Overfit control:** N_eff floor 88 CORE · purged walk-forward 90 CORE · nested CV 60 REJECT(data-hungry) · **shrinkage-to-prior 91 CORE** · ensemble-disagreement abstain 86 CORE · **PBO/deflated-Sharpe 89 CORE** · MDL penalty 57 COND.

**Training:** single pass 42 REJECT(contamination) · dependency-ordered+Σ 90 CORE · iterative EM 55 REJECT(leakage risk) · curriculum 60 COND.

**Non-breakage:** additive+gated+identity 92 CORE · shadow/replay 84 FOLD · champion-challenger 66 COND(live-money) · canary 64 COND(live-money).

**Failure posture:** floor-and-abstain 85 (subsumed) · **fallback cascade cell→parent→regime→neutral 90 CORE** · graceful-degrade 80 FOLD.