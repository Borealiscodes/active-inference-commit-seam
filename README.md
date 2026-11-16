# 🌉 active-inference-commit-seam

A zero-dependency Python architecture that separates **exploratory active inference** (Salience Δ, Structural Resonance Φ, and uncertainty-minimizing queries) from a **fail-closed cryptographic commit ledger** (`Record ≠ Admit ≠ Commit`), with an optional telemetry adapter for [`stell2026/Causa`](https://github.com).

> ### 🚧 Project Status: Untested Reference Prototype
> **Transparency Note:** The modules and test harnesses in this repository were drafted as a clean-room architectural blueprint and **have not yet been executed or verified end-to-end**. Please run the local `unittest` suite to verify behavior before integrating into any research workflow.

---

## 🎯 Why This Repository Exists: Putting Salience & Active Inference on the Right Side of the Seam

AI safety architectures often fall into one of two traps:
1. **Unconstrained Exploratory Agents:** Systems driven by salience, semantic similarity ("resonance"), or active-inference loops are great at spotting subtle anomalies and deciding *what to investigate next*—but if allowed to write directly to memory, high salience or repeated claims can masquerade as verified evidence.
2. **Blind Deterministic Gates:** Purely deterministic verifiers (`SHA-256` hashes, exact fractions, DAG cycle checks) are incorruptible—but they have no compass to tell you *which* of 10,000 paragraphs hides a critical contradiction or *what* missing record to pull next.

**`active-inference-commit-seam`** keeps both capabilities by placing a strict **epistemic and cryptographic seam** between them:

```text
[ PROPOSAL SIDE: EXPLORATORY & ACTIVE INFERENCE ]
  • Salience (Δ): Surprisal-based triage (quantized to exact rationals)
  • Resonance (Φ): Cross-silo structural similarity (exact Jaccard fractions)
  • Active Inference: Formulates next queries to resolve missing evidence
  • Epistemic Tag: Strictly DERIVED (never OBSERVED)
                         │
            ═════════════╧═════════════  <-- THE SEAM (Stage -> Admit -> Commit)
                         │
[ COMMIT SIDE: DETERMINISTIC LEDGER & CAUSA TELEMETRY ]
  • CommitLedger: Verifies SHA-256 source ancestry & Non-Self-Warranting Law
  • CAUSA Adapter (Optional): Audits directional ownership & expression congruence
  • Appends immutable DERIVED_VERIFIED records or tombstones rejections
```

### The Golden Rule Across the Seam
* **Salience (Δ), Resonance (Φ), and Active Inference** decide *where to look* and *what to hypothesize*.
* **Cryptographic `SHA-256` provenance and exact rational math** decide *what gets committed* as verified fact.

---

## 📂 Repository Structure

```text
active-inference-commit-seam/
├── README.md                    # Seam architecture, license boundary & quickstart
├── pyproject.toml               # Zero-dependency manifest + optional [research] CAUSA extra
├── src/
│   ├── active_inference_seam.py # Core MIT seam: ExploratoryProposer + fail-closed CommitLedger
│   └── causa_seam_adapter.py    # Optional adapter for OwnershipTracker, congruence & baselines
└── tests/
    └── test_seam.py             # Standard-library unittest suite (runs with or without CAUSA)
```

---

## 🚀 Quickstart

### 1. Run the Core Zero-Dependency Seam Demo (Python 3.10+)
No external packages are required to run the core exploratory proposer and fail-closed commit ledger:

```bash
python3 src/active_inference_seam.py
```

This runs an end-to-end demonstration showing:
1. **Salience & Resonance Triage:** Filters routine noise and prioritizes high-surprisal cross-silo anomalies with follow-up active-inference queries.
2. **Fail-Closed Provenance Rejection:** Blocks an altered quote even when disguised with an extreme salience score (`99/1`).
3. **Non-Self-Warranting Law:** Rejects duplicate repetitions of an already-committed claim so repetition never manufactures extra warrant.

### 2. Optional: Enable `CAUSA` Causal Agency Telemetry (Research Use)
To audit whether your active-inference policy actually steered state transitions (`directional_ownership`) and whether rationale text matches internal `[salience, resonance, certainty]` coordinates (`expression_congruence`), install [`stell2026/Causa`](https://github.com):

```bash
git clone https://github.com
pip install -e ./Causa
python3 src/causa_seam_adapter.py
```

### 3. Run the Unit Test Suite
```bash
python3 -m unittest discover -s tests -v
```

---

## ⚖️ Dual-Boundary Licensing Note

To prevent non-commercial copyleft terms from bleeding into clean-room baseline code, this repository maintains a strict boundary:
* **Core Seam (`src/active_inference_seam.py` & `tests/`):** **MIT License** — zero external dependencies, free for any commercial or non-commercial use.
* **Optional Adapter (`src/causa_seam_adapter.py`):** Imports [`stell2026/Causa`](https://github.com), which is governed by the **CAUSA Non-Commercial License 1.1** (free for personal, educational, and research use; commercial deployment requires written permission from the `CAUSA` author).
