#!/usr/bin/env python3
"""Standard-library unit tests for active-inference-commit-seam (runs with or without CAUSA)."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import causa_seam_adapter
from active_inference_seam import (
    CommitLedger,
    ExploratoryProposer,
    ObservedChunk,
    StagedProposal,
)


@dataclass
class _MockScore:
    score: float
    defined: bool = True
    per_dimension: list[float] | None = None


class _MockTracker:
    def __init__(self, history_size: int = 64, event_threshold: float = 0.30) -> None:
        self.pending: tuple[str, list[float], list[float]] | None = None

    def register_intent(self, name: str, before: list[float], predicted: list[float]) -> None:
        self.pending = (name, before, predicted)

    def observe(self, after: list[float]) -> _MockScore | None:
        if self.pending is None:
            return None
        self.pending = None
        return _MockScore(score=0.8125, defined=True)


class TestActiveInferenceCommitSeam(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = CommitLedger()
        self.docs = [
            ObservedChunk.from_raw(
                "doc-01",
                "https://example.org",
                "Routine quarterly scheduling notice for building inspection.",
            ),
            ObservedChunk.from_raw(
                "doc-02",
                "https://example.org",
                "Retroactive jurisdiction transfer executed without statutory warrant or notice.",
            ),
        ]
        for doc in self.docs:
            self.ledger.ingest_observation(doc)

        self.proposer = ExploratoryProposer(prior_token_counts={"routine": 50, "quarterly": 40})

    def test_salience_and_resonance_prioritize_anomaly(self) -> None:
        proposals = self.proposer.propose_from_corpus(
            self.docs,
            reference_pattern="retroactive transfer without statutory warrant during appeal",
            top_k=1,
        )
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].target_chunk_id, "doc-02")
        self.assertEqual(proposals[0].kind, "DERIVED")
        self.assertIn("appeal", proposals[0].active_query)

    def test_commit_ledger_blocks_hallucination_and_duplicate_warrant(self) -> None:
        # 1. High salience cannot bypass verbatim SHA-256 verification
        forged = StagedProposal(
            proposal_id="prop-forged",
            target_chunk_id="doc-02",
            quoted_text="Retroactive jurisdiction transfer approved with statutory warrant.",
            salience_delta=Fraction(100, 1),
            resonance_phi=Fraction(1, 1),
            active_query="None",
            rationale="Altered quote.",
        )
        res_forged = self.ledger.admit_and_commit(forged)
        self.assertEqual(res_forged["status"], "REJECTED")
        self.assertIn("ProvenanceError", res_forged["reason"])

        # 2. Valid proposal commits once, then duplicate repetition is rejected
        valid = self.proposer.propose_from_corpus(
            self.docs,
            reference_pattern="retroactive transfer without statutory warrant",
            top_k=1,
        )[0]
        first_commit = self.ledger.admit_and_commit(valid)
        self.assertEqual(first_commit["status"], "COMMITTED")

        second_commit = self.ledger.admit_and_commit(valid)
        self.assertEqual(second_commit["status"], "REJECTED")
        self.assertIn("NonSelfWarrantingError", second_commit["reason"])

    def test_tampered_observation_substrate_fails_closed(self) -> None:
        tampered = ObservedChunk(
            chunk_id="doc-tampered",
            source_uri="https://example.org",
            text="Original text.",
            sha256="0" * 64,
        )
        with self.assertRaisesRegex(ValueError, "Integrity Failure"):
            self.ledger.ingest_observation(tampered)

    def test_causa_seam_bridge_with_mocked_telemetry(self) -> None:
        with (
            patch.object(causa_seam_adapter, "CAUSA_AVAILABLE", True),
            patch.object(causa_seam_adapter, "OwnershipTracker", _MockTracker, create=True),
            patch.object(
                causa_seam_adapter,
                "Episode",
                lambda before, predicted, after: (before, predicted, after),
                create=True,
            ),
            patch.object(
                causa_seam_adapter,
                "CongruenceConfig",
                lambda scale=1.0: scale,
                create=True,
            ),
            patch.object(
                causa_seam_adapter,
                "expression_congruence",
                lambda exp, internal, cfg: _MockScore(score=0.75, per_dimension=[0.8, 0.7, 0.75]),
                create=True,
            ),
        ):
            bridge = causa_seam_adapter.CausaSeamBridge(ledger=self.ledger, proposer=self.proposer)
            outcome = bridge.run_audited_step(
                self.docs,
                reference_pattern="retroactive transfer without statutory warrant",
            )
            self.assertEqual(outcome["commit"]["status"], "COMMITTED")
            self.assertTrue(outcome["causa"]["ownership_defined"])
            self.assertEqual(outcome["causa"]["ownership_score"], 0.8125)
            self.assertEqual(outcome["causa"]["congruence_score"], 0.75)


if __name__ == "__main__":
    unittest.main()
