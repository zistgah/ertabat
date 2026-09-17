"""Work packets. This is the orchestration surface.

A packet is one unit of work another agent — or another person — can take away
and finish without asking a question, because it carries its own inputs, its own
interface and, above all, its own acceptance test. The test is the contract: the
packet is done when the named command passes, and not when the work reads well.

Labels follow the estate's routing convention: capability labels (needs:code,
needs:proof, needs:testing, needs:ontology, needs:visual, needs:legal,
needs:human), never a model name. Which agent takes a packet is a dispatch
decision by the human, not a property of the work.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field


@dataclass(frozen=True)
class Packet:
    id: str
    title: str
    needs: tuple
    why: str
    inputs: tuple
    interface: str
    acceptance: str
    forbidden: tuple = field(default_factory=lambda: (
        "inventing a numeric constant that is not derived or cited",
        "returning a value where the module currently returns Unknown, without "
        "naming the source of the value",
        "a driver that synthesises samples instead of raising NotFitted",
    ))

    def as_dict(self):
        return asdict(self)


PACKETS = (
    Packet("ATM-1", "Populate ITU-R P.838 rain coefficients",
           ("needs:proof", "needs:code"),
           "Every Ku and Ka budget in this repo returns Unknown until the k/alpha "
           "table exists. This single file unblocks the whole high-band tier.",
           ("ITU-R P.838-3 tables 1 and 2",),
           "data/itu_p838.json per ertabat.link.atmosphere.SCHEMA_P838, with "
           "populated_by and retrieved_utc filled in",
           "python3 -m pytest tests/test_atmosphere.py -k populated  "
           "(skips while the table is absent, runs and must pass once present)"),
    Packet("ATM-2", "Populate ITU-R P.676 gaseous absorption coefficients",
           ("needs:proof", "needs:code"),
           "Gaseous absorption is the term that is always omitted and always "
           "there; above 10 GHz it decides whether the link closes.",
           ("ITU-R P.676 line-by-line or approximate method",),
           "data/itu_p676.json per SCHEMA_P676",
           "python3 -m pytest tests/test_atmosphere.py -k gaseous"),
    Packet("ATM-3", "Implement P.618 tropospheric scintillation",
           ("needs:code", "needs:proof"),
           "Scintillation is what actually breaks high-order QAM on a low "
           "elevation pass, and the module currently declares it unimplemented.",
           ("ITU-R P.618 section 2.4.1", "N_wet for the site from P.453"),
           "ertabat.link.atmosphere.scintillation_fade_db returns a number when "
           "n_wet is supplied and Unknown when it is not",
           "python3 -m pytest tests/test_atmosphere.py -k scintillation"),
    Packet("DRV-1", "Bind a real RTL-SDR driver",
           ("needs:code", "needs:testing"),
           "The first real receiver in the HAL: it makes every downstream "
           "claim testable against a captured signal instead of a stub.",
           ("librtlsdr", "skills/agents/driver-authoring.md"),
           "ertabat.hal.registry.register('rtlsdr-v3', factory) with a class "
           "implementing RadioDevice; read_iq returns real samples or raises",
           "python3 -m pytest tests/test_hal.py  (the honesty tests must still "
           "pass for every unbound device)"),
    Packet("DRV-2", "Bind a Pluto or USRP driver with GPSDO timing",
           ("needs:code", "needs:testing"),
           "Timing discipline is the precondition for any NTN experiment; a "
           "free-running oscillator cannot hold a PRACH window.",
           ("libiio or UHD", "a 10 MHz reference"),
           "As DRV-1, plus a reference_locked() capability that is False when "
           "the reference is absent",
           "python3 -m pytest tests/test_hal.py -k reference"),
    Packet("BOM-1", "Add a distributor price provider",
           ("needs:code",),
           "Coverage of Indian and Chinese supply is thin, which is where these "
           "builds are actually sourced.",
           ("distributor API documentation", "skills/agents/provider-authoring.md"),
           "A PriceProvider subclass in ertabat/bom/providers.py registered in "
           "REGISTRY; key read by file path only",
           "python3 -m pytest tests/test_bom.py  (including the failure-path "
           "tests: a 403, an empty result and a malformed body all end Unknown)"),
    Packet("NTN-1", "Widen the srsRAN or OpenAirInterface HARQ and RACH timers",
           ("needs:code", "needs:testing"),
           "ertabat computes the k_offset and the RACH window a given orbit needs; "
           "the stacks have to be patched to accept them.",
           ("srsRAN or OAI source", "ertabat ntn timing output for the target orbit"),
           "A patch series against the upstream tree with the computed values, "
           "no whole-file regeneration, exact anchors",
           "ertabat ntn --altitude <km> --elevation <deg> agrees with the patched "
           "constants; the patch applies cleanly to a pinned upstream commit"),
    Packet("SOTA-1", "Neuromorphic OBP: fault behaviour under SEU",
           ("needs:ontology", "needs:proof"),
           "The track is at SPEC and cannot be promoted without this.",
           ("a bound part with a TID and SEU rating",),
           "A written model of scheduler behaviour after an upset, and the "
           "measurement that would distinguish it from a bad link",
           "ertabat sota --promote obp-neuromorphic --to MODEL --evidence <path> "
           "must be accepted, which requires the evidence to exist"),
)


def by_label(label: str):
    return [p for p in PACKETS if label in p.needs]


def to_json():
    return json.dumps([p.as_dict() for p in PACKETS], indent=2)


def to_markdown():
    o = ["# Work packets", "",
         "Each packet is complete: inputs, interface, and the command that "
         "decides whether it is done. Take one, finish it, prove it.", ""]
    for p in PACKETS:
        o += [f"## {p.id} — {p.title}", "",
              f"**Labels** {' · '.join(p.needs)}", "",
              p.why, "",
              "**Inputs**"] + [f"- {i}" for i in p.inputs] + [
              "", f"**Interface** {p.interface}", "",
              f"**Accepted when** `{p.acceptance}`", "",
              "**Not acceptable**"] + [f"- {f}" for f in p.forbidden] + [""]
    return "\n".join(o)
