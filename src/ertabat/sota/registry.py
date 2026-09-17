"""The state-of-the-art tier, carried at its real maturity.

Each track states what ertabat can compute for it TODAY, what it cannot, and the
one question that has to be answered before the track becomes engineering. The
status ladder is the same one the collaborative programmes use, so a claim can
never be read at a higher rung than it was entered at.

SPEC            the idea is described; nothing here computes it
MODEL           a closed-form or numerical model exists in this repo
SIMULATED       the model has been run against synthetic input
BENCH           measured on hardware on someone's bench
FLIGHT          measured in orbit

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

LADDER = ("SPEC", "MODEL", "SIMULATED", "BENCH", "FLIGHT")


@dataclass(frozen=True)
class Track:
    key: str
    title: str
    status: str
    displaces: str
    computable_today: tuple
    not_computable: tuple
    open_question: str
    packet: str

    def as_dict(self):
        return asdict(self)


TRACKS = {t.key: t for t in (
    Track("obp-neuromorphic",
          "Regenerative on-board processing with neuromorphic inference",
          "SPEC",
          "ground-computed scheduling and beamforming",
          ("payload power and thermal budget from a declared bus budget",
           "the O-RAN split that puts the scheduler on board (ntn.oran option2)"),
          ("spiking-network accuracy under radiation-induced bit flips",
           "energy per inference for a specific part — no part is bound here"),
          "What does the scheduler do in the seconds after an SEU, and how is "
          "that different from what it does when the link is merely bad?",
          "SOTA-1"),
    Track("optical-isl",
          "Optical inter-satellite links and hybrid RF/optical switching",
          "SPEC",
          "RF-only backhaul between satellites",
          ("geometric range and pointing rate between two orbits",
           "the RF fallback budget the optical link switches to"),
          ("acquisition and tracking loop performance",
           "cloud-blockage statistics for a ground site — needs a climatology"),
          "At what fade depth and over what horizon does the switch to RF pay "
          "for itself, given that the decision must be made before the fade?",
          "SOTA-2"),
    Track("cell-free-mimo",
          "Cell-free massive MIMO across a satellite swarm",
          "SPEC",
          "single-satellite spot beams with a handover every beam dwell",
          ("beam dwell and handover cadence that the scheme claims to remove",
           "phase-coherence budget implied by a stated clock stability"),
          ("joint precoding gain for a real constellation geometry",
           "inter-satellite ranging error budget"),
          "What clock and ranging error turns constructive interference at the "
          "user into destructive interference, and how often is that exceeded?",
          "SOTA-3"),
    Track("semantic",
          "Semantic and goal-oriented transmission",
          "SPEC",
          "Shannon-limited bit transport",
          ("the bit-rate budget the semantic scheme is measured against",),
          ("reconstruction fidelity — which is the whole claim",
           "behaviour on inputs outside the shared model's training set"),
          "What is the failure mode when the two models drift apart, and how "
          "does the receiver know that it has happened rather than trusting a "
          "confident reconstruction?",
          "SOTA-4"),
    Track("qkd",
          "Quantum key distribution over the space segment",
          "SPEC",
          "classical key exchange over the same link",
          ("the classical link budget the QKD channel rides beside",),
          ("secret key rate under loss and background counts",
           "detector dark-count and after-pulse behaviour in orbit"),
          "What is the key rate after finite-key correction at the loss this "
          "geometry actually gives, rather than at the loss in the abstract?",
          "SOTA-5"),
)}


def census():
    return {k: t.status for k, t in TRACKS.items()}


def promote_check(track_key: str, claimed: str, evidence_path: str = None):
    """A rung is claimed with evidence or not at all."""
    from .. import Unknown
    t = TRACKS.get(track_key)
    if not t:
        return Unknown(f"no SOTA track {track_key}", tuple(TRACKS))
    if claimed not in LADDER:
        return Unknown(f"{claimed} is not a rung", LADDER)
    if LADDER.index(claimed) > LADDER.index(t.status) and not evidence_path:
        return Unknown(f"{track_key} is recorded at {t.status}; {claimed} needs "
                       f"evidence in the tree", ("evidence_path",))
    return {"track": track_key, "recorded": t.status, "claimed": claimed,
            "evidence": evidence_path}
