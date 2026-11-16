#!/usr/bin/env python3
"""
causa_seam_adapter.py
Optional research adapter bridging `active_inference_seam.py` (MIT) with `stell2026/Causa`
(CAUSA Non-Commercial License 1.1) to audit causal agency and utterance-state alignment
across the proposal-to-commit seam.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from active_inference_seam import (
    CommitLedger,
    ExploratoryProposer,
    ObservedChunk,
)

try:
    from causa import (
        CongruenceConfig,
        Episode,
        OwnershipTracker,
        expression_congruence,
        permutation_baseline,
    )
    CAUSA_AVAILABLE = True
except ImportError:
    CAUSA_AVAILABLE = False


# ============================================================================
# 1. NUMERIC STATE & UTTERANCE PROJECTION ADAPTERS
# ============================================================================

def state_to_vector(salience_delta: Fraction, resonance_phi: Fraction, uncertainty: Fraction) -> list[float]:
    """
    Project exact rational epistemic state [Δ, Φ, U] into bounded [0.0, 1.0] coordinates
    for CAUSA geometric comparison.
    """
    # Normalize salience (0..10 bits -> 0..1), resonance (already 0..1), uncertainty (0..1)
    s_norm = min(max(float(salience_delta) / 10.0, 0.0), 1.0)
    r_norm = min(max(float(resonance_phi), 0.0), 1.0)
    u_norm = min(max(float(uncertainty), 0.0), 1.0)
    return [s_norm, r_norm, u_norm]


def rationale_to_vector(rationale: str) -> list[float]:
    """
    Domain-specific projection mapping a natural-language rationale onto the same 3D
    [salience_claim, resonance_claim, certainty_claim] coordinate space in [0.0, 1.0].
    """
    tokens = set(re.findall(r"[a-z0-9]+", rationale.lower()))

    high_salience_cues = {"critical", "anomaly", "retroactive", "without", "high", "urgent", "breach"}
    high_resonance_cues = {"match", "pattern", "parallel", "cross", "echo", "resonance", "aligned"}
    high_certainty_cues = {"verified", "exact", "confirmed", "proven", "accounted", "complete"}

    s_claim = min(len(tokens & high_salience_cues) / 2.0, 1.0)
    r_claim = min(len(tokens & high_resonance_cues) / 2.0, 1.0)
    c_claim = min(len(tokens & high_certainty_cues) / 2.0, 1.0)
    return [s_claim, r_claim, c_claim]


# ============================================================================
# 2. CAUSA-INSTRUMENTED SEAM BRIDGE
# ============================================================================

@dataclass
class CausaSeamBridge:
    """
    Instruments the seam between ExploratoryProposer and CommitLedger:
      1. Tracks directional ownership across intent -> outcome transitions.
      2. Checks expression congruence between internal state and rationale text.
      3. Accumulates episodes for permutation_baseline falsifiability testing.
      4. Enforces CommitLedger SHA-256 provenance before any record is persisted.
    """
    ledger: CommitLedger
    proposer: ExploratoryProposer
    congruence_threshold: float = 0.50
    tracker: Any = field(init=False)
    episodes: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not CAUSA_AVAILABLE:
            raise RuntimeError(
                "stell2026/Causa is not installed. Install via `pip install -e /path/to/causa` "
                "(subject to CAUSA Non-Commercial License 1.1)."
            )
        self.tracker = OwnershipTracker(history_size=64, event_threshold=0.30)

    def run_audited_step(
        self,
        chunks: list[ObservedChunk],
        reference_pattern: str,
        uncertainty_before: Fraction = Fraction(4, 5),
    ) -> dict[str, Any]:
        # 1. Measure pre-action internal state [Δ_before, Φ_before, U_before]
        state_before = state_to_vector(Fraction(0, 1), Fraction(0, 1), uncertainty_before)

        # 2. Generate top active-inference proposal
        proposals = self.proposer.propose_from_corpus(chunks, reference_pattern=reference_pattern, top_k=1)
        if not proposals:
            return {"status": "NO_PROPOSAL", "causa": None, "commit": None}

        prop = proposals[0]

        # Predict target state: salience & resonance rise to proposal levels, uncertainty drops
        predicted_uncertainty = max(Fraction(1, 1) - prop.resonance_phi, Fraction(0, 1))
        state_predicted = state_to_vector(prop.salience_delta, prop.resonance_phi, predicted_uncertainty)

        # Register single-use intention in OwnershipTracker
        self.tracker.register_intent(prop.active_query, state_before, state_predicted)

        # 3. Cross the deterministic CommitLedger seam (SHA-256 + Non-Self-Warranting Law)
        commit_result = self.ledger.admit_and_commit(prop)

        # 4. Observe post-seam outcome state (if rejected, uncertainty remains high)
        if commit_result["status"] == "COMMITTED":
            actual_uncertainty = predicted_uncertainty
        else:
            actual_uncertainty = uncertainty_before

        state_after = state_to_vector(prop.salience_delta, prop.resonance_phi, actual_uncertainty)

        # Consume intention and record episode for permutation baseline
        ownership = self.tracker.observe(state_after)
        self.episodes.append(Episode(before=state_before, predicted=state_predicted, after=state_after))

        # 5. Evaluate expression congruence between rationale text and internal post-state
        expressed_vec = rationale_to_vector(prop.rationale)
        congruence = expression_congruence(
            expressed_vec,
            state_after,
            CongruenceConfig(scale=1.0),
        )

        return {
            "proposal_id": prop.proposal_id,
            "commit": commit_result,
            "causa": {
                "ownership_score": round(ownership.score, 4) if ownership and ownership.defined else None,
                "ownership_defined": bool(ownership.defined) if ownership else False,
                "congruence_score": round(congruence.score, 4),
                "congruence_per_dim": {
                    dim: round(val, 4)
                    for dim, val in zip(["salience", "resonance", "certainty"], congruence.per_dimension)
                },
                "congruence_flag": congruence.score < self.congruence_threshold,
            },
        }

    def evaluate_baseline(self, n_permutations: int = 1000, seed: int = 0) -> str:
        """
        Falsifiability check: compares observed directional ownership against shuffled
        (intention, outcome) pairings on the exact same state space.
        """
        if len(self.episodes) < 2:
            return "Insufficient episodes for permutation baseline (need >= 2)."
        report = permutation_baseline(self.episodes, n_permutations=n_permutations, seed=seed)
        return report.summary()


# ============================================================================
# 3. STANDALONE DEMO (WHEN CAUSA IS INSTALLED)
# ============================================================================

if __name__ == "__main__":
    if not CAUSA_AVAILABLE:
        print("CAUSA not installed in this environment; adapter syntax verified.")
    else:
        ledger = CommitLedger()
        docs = [
            ObservedChunk.from_raw(
                "doc-01",
                "https://example.org",
                "Routine administrative scheduling notice for quarterly maintenance.",
            ),
            ObservedChunk.from_raw(
                "doc-02",
                "https://example.org",
                "Retroactive jurisdiction transfer executed without notice or statutory warrant.",
            ),
        ]
        for d in docs:
            ledger.ingest_observation(d)

        proposer = ExploratoryProposer(prior_token_counts={"routine": 50, "administrative": 40})
        bridge = CausaSeamBridge(ledger=ledger, proposer=proposer)

        step_1 = bridge.run_audited_step(docs, "retroactive transfer without statutory warrant")
        step_2 = bridge.run_audited_step(docs, "routine maintenance schedule")

        print(json.dumps({"step_1": step_1, "step_2": step_2}, indent=2))
        print("Permutation Baseline:", bridge.evaluate_baseline(n_permutations=500, seed=42))
