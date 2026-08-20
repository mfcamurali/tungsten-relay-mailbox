# TUNGSTEN — Quant Requirements Specification
### Build target for an adaptive, self-regulating, low-maintenance MQL4 EA (XAU/USD)
*Scope: what "done" means for a system that adapts and protects itself, rather than one that is assumed to be permanently correct. Every requirement is testable. "Self-regulating" here means the system detects its own failure and stands down — not that it is infallible.*

---

## 0. Governing principles (non-negotiable)

- **P1 — Fail safe, not silent.** Any unhandled condition halts new entries and logs, never trades blind. Absence of a signal is a valid, safe output.
- **P2 — Correctness before profitability.** Wiring, math, and state must be provably correct independent of whether any given regime is currently profitable. These are two separate guarantees; the code owns the first, the market owns the second.
- **P3 — Every line in sync, forward-only.** No version regressions. A change to any shared constant, enum, or buffer index propagates to every consumer in the same commit. No orphaned code paths.
- **P4 — Observable at all times.** Every decision (entered/skipped/why) is reconstructable from logs after the fact. If you can't explain a trade from the log alone, the log is incomplete.
- **P5 — Bounded adaptation.** The system may retune within hard-coded guardrails; it may never adapt its way past a risk limit. Learning changes *preferences*, never *safety ceilings*.

---

## 1. Adaptive / learning subsystem

- **1.1 Online performance memory.** Per-regime, per-session, per-signal-pattern rolling stats: win rate, expectancy (E[R]), profit factor, sample count. Use decay-weighted (OWA/EMA) so recent behaviour dominates but history isn't erased.
- **1.2 Learn from losses AND misses.** Record not only closed-trade outcomes but *skipped* setups and their hypothetical result (ghost/shadow evaluation). Missed-opportunity cost feeds threshold relaxation the same way losses feed tightening.
- **1.3 Association formation.** Maintain a conditional-probability table keyed on `regime × score-bucket × pattern × session × volatility-bucket` (the existing 6-D ProbDB). Every closed and ghosted trade updates the matching cell. Cells below a minimum sample count (e.g. n<30) are treated as *unknown*, not as zero — unknown routes to conservative defaults, never to confident action.
- **1.4 Minimum-evidence gating.** No learned parameter influences live sizing or entry until its supporting sample crosses a significance floor. Below the floor, fall back to the hard-coded prior. This is what stops the system "learning" noise and blowing up on a lucky streak.
- **1.5 Bounded parameter drift.** Every adaptive parameter has `[min, max, max-step-per-update]`. An update that would exceed the step clamp is clamped and flagged. Prevents runaway feedback loops.
- **1.6 Reversible learning.** Learned state is versioned and checkpointed. If post-update live performance degrades past a threshold within a defined window, auto-rollback to the last good checkpoint.

---

## 2. Regime intelligence & "waiting"

- **2.1 Explicit regime classifier** (the existing 9-state Bayesian model) runs every bar; outputs a belief distribution, not a single label. Conviction = f(distribution sharpness).
- **2.2 Uncertainty state.** When no regime holds majority belief, the system enters an explicit `UNCERTAIN` state → reduce size or stand down entirely. "Waiting" is a first-class action, not the absence of one.
- **2.3 Regime-transition hostility.** Maintain the transition matrix; when the current regime's most-likely *next* state is historically hostile to the open direction (R6/R7 trim logic), pre-emptively trim conviction or exit. Edge decays *before* the regime visibly flips — trade the transition probability, not just the current label.
- **2.4 Regime-specific everything.** SL/TP, sizing, thresholds, and expectancy are all conditioned on regime. No global constant that ignores regime is permitted in the entry/exit path.

---

## 3. Signal engine

- **3.1 Multi-layer confirmation with IC weighting.** Each of the 14 layers contributes a weighted vote; weights are the layer's information coefficient, re-estimated online (§1). Dead/negative-IC layers auto-down-weight toward zero.
- **3.2 Instrument-relative units everywhere.** No raw pip/price constants. Everything expressed in ATR multiples or instrument-relative terms so the logic survives symbol/volatility shifts without re-tuning.
- **3.3 MTF coherence.** M15/H1/H4 trend agreement checked and must not contradict the entry direction. Disagreement is a veto or a size penalty, never ignored.
- **3.4 Conviction margin gate.** Entry requires conviction to clear the threshold by a *margin*, not merely touch it. The margin itself scales with recent expectancy of the active regime.
- **3.5 No blindspot layers.** Every signal layer must define its output for degenerate inputs (flat market, gap, insufficient history). A layer that can't compute returns *abstain*, which is neutral-weighted — never a default bullish/bearish tilt.

---

## 4. Execution & order management

- **4.1 Safe order send.** Wrap every `OrderSend`/`OrderModify` with: pre-trade margin check, stop-level/freeze-level compliance, retry with re-quote handling (bounded retries, gate-specific — no blind re-fires), and full error-code branching. Every MT4 trade error code has an explicit handler.
- **4.2 Slippage & spread guard.** Reject or re-price entries when spread exceeds a regime-aware ceiling. Widen ceiling logic for news windows rather than trading into a 40-pip gold spread.
- **4.3 Stop integrity.** Hard invariant: `SL` is always set, always the correct side, and `TP ≥ SL × RR_min` (1.5×). Assert on every order; a violated invariant blocks the send and logs a defect.
- **4.4 Half-Kelly sizing with floors/ceilings.** Lot size = f(edge estimate, account equity, regime confidence), clamped to `[min_lot, max_risk_%_of_equity]`. Kelly fraction never exceeds ½; unknown edge → minimum size.
- **4.5 Idempotent tick handling.** Re-entrancy guard on `OnTick` that *always* releases (the SLS21 leak class). No lock may persist across a return path. Verified by a guaranteed-release pattern, not by hoping every branch resets it.

---

## 5. Risk & capital preservation (the hard ceilings)

- **5.1 Per-trade risk cap** — fixed % of equity, un-overridable by any learned parameter.
- **5.2 Daily loss halt** — cumulative daily drawdown ≥ threshold → flatten new-entry permission until next session.
- **5.3 Consecutive-loss circuit breaker** — N losses in a row → cooldown + size reduction until a recovery condition is met.
- **5.4 Equity-floor kill switch** — absolute account floor below which the EA disables itself and alerts. Non-negotiable, checked every tick.
- **5.5 Correlation/exposure cap** — max simultaneous risk across open positions (relevant if ever multi-symbol).
- **5.6 News blackout** — configurable hard stand-down around high-impact events (this is what the `TUNGSTEN_events.csv` feed is for). Trading resumes only after a post-event settle window.

---

## 6. Self-monitoring, drift & degradation (this is "self-regulating")

- **6.1 Live-vs-expected tracking.** Continuously compare realised win rate / expectancy against the model's own forecast for the active regime. Divergence beyond tolerance = degradation signal.
- **6.2 Drift detection.** Statistical test (e.g. CUSUM / rolling-window WR collapse) on live results. On detected drift: auto-reduce size → quarantine the offending regime cell → require re-qualification before full size returns.
- **6.3 Auto-quarantine & re-promotion.** Any regime/pattern whose live OOS WR drops below the floor (e.g. <55%) is benched. It must re-earn its place via the same ghost/OOS gates a new pattern faces (p6Met ≥ 3/6). Promotion is never automatic on a small rebound.
- **6.4 Health heartbeat.** Periodic self-check: history available, indicators returning valid values, spread sane, connection alive, state file writable. Any failure → safe mode + alert.
- **6.5 Self-audit log.** On a schedule, the EA writes a summary of its own state: active regime, live vs expected, quarantine list, parameter drift, open risk. This is the artifact you read *instead of* re-reading the code.

---

## 7. Robustness / no-stuck-states

- **7.1 Cold start & gap recovery.** Correct behaviour on first tick, after weekend gap, after reconnect, after terminal restart, and with insufficient bar history. Never assume `Bars` is large enough — bound every historical loop.
- **7.2 Bad-data tolerance.** Zero/negative ATR, zero volume, missing MTF bars, `iMA`/`iMACD` returning 0 on unbuilt history — each has a defined fallback. No division without a guard.
- **7.3 No dead code on live paths.** Every calibration/learning branch reachable in production is proven reachable (the SLS21 `g_CalibSilent` / dangling-if class). No loss-side learning branch may be unreachable.
- **7.4 Deterministic exits.** Every state has a defined transition out. No lock, flag, or mode (Ghost/Discovery/Recovery) can be entered without a guaranteed release condition.
- **7.5 Lookahead-free.** Every historical loop indexes in the correct temporal direction. No future bar leaks into a live threshold (the SLS21 reversed-loop class). Verified explicitly.

---

## 8. State, persistence & logging

- **8.1 Atomic persistence.** All state writes via temp-file + rename (already the pattern for the CSV). No half-written state files.
- **8.2 Versioned state schema.** State files carry a schema version; loader migrates or safely rejects mismatches rather than mis-parsing.
- **8.3 Full decision log.** Per bar/trade: inputs, regime belief, layer votes, conviction, gate outcomes, and reason-for-skip. Sufficient to replay any decision offline.
- **8.4 Crash-consistent.** Killing the terminal mid-tick must never corrupt state or orphan a position without its stop.

---

## 9. Validation & promotion gates (before any parameter goes live)

- **9.1 Ghost / OOS gauntlet.** Chronological, non-overlapping, unlimited-OOS ghost evaluation. A pattern promotes only on p6Met ≥ 3/6 and OOS WR ≥ floor.
- **9.2 Walk-forward, not in-sample fit.** All edge claims validated walk-forward. In-sample performance is never a promotion criterion on its own.
- **9.3 Regime-stratified acceptance.** A parameter must clear its gates *within each regime it affects*, not just on pooled data.
- **9.4 Change-safety gate.** No commit merges unless it compiles zero-error/zero-warning AND passes a correctness self-test harness (invariants in §4.3, release proofs in §7.4, lookahead check in §7.5).

---

## 10. Human oversight interface (minimal, but never zero)

- **10.1 One-glance status.** A single dashboard/log line: mode, equity, open risk, active regime, live-vs-expected, quarantine count, last alert. If everything is green you do nothing; that's the low-maintenance payoff.
- **10.2 Alerting.** Push/email on: kill-switch trip, drift-detected, quarantine event, heartbeat failure, or manual-attention flag. The system asks for you only when it has already protected you.
- **10.3 Manual override.** A hard external flag (file/global var) that disables new entries immediately, independent of internal state. You always have the last word.

---

## 11. MQL4 / MT4 platform constraints

- **11.1 Tick-budget aware.** Full 14-layer + ProbDB evaluation must complete well within a tick on `OnTick`; heavy recomputation gated to new-bar events, cached otherwise.
- **11.2 No external file dependencies at runtime** beyond the events CSV and state files. (Confirmed: current build uses only native indicators — no `iCustom`, so nothing to go missing on deploy.)
- **11.3 Broker-agnostic.** No hard-coded digits, point values, stop levels, or contract sizes — all queried from `MarketInfo`/symbol properties at init.
- **11.4 Account-type aware.** Correct behaviour on ECN (separate SL/TP set after fill) vs instant-execution brokers.

---

## Acceptance definition ("done")

The build is **done** when:
1. Compiles zero-error, zero-warning.
2. Every indicator call and buffer index verified against its consumer.
3. Every §4.3 / §5 / §7.4 invariant holds under a fault-injection test (bad ticks, disconnect, gap, restart, insufficient history).
4. Every learning path is reachable, bounded, reversible, and evidence-gated.
5. The self-monitoring layer (§6) demonstrably halts the system in a synthetic degradation test.
6. A decision can be fully reconstructed from logs alone.

**Done means: it will not break, get stuck, trade blind, or need bug-fixing.** It does **not** mean it will be profitable in every regime — that is what §6 detects and §5 contains. The system's job when its edge decays is to *notice and stand down automatically*, which is the actual definition of "doesn't need constant tinkering."
