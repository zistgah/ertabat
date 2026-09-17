"""O-RAN functional split in orbit: what each option costs on the feeder link.

The split argument is usually made in prose. It is really a bit-rate argument,
so it is computed here: Option 8 carries raw I/Q and needs a feeder link an
order of magnitude wider than the traffic it serves.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

from .. import Unknown

SPLITS = {
    "option8": {
        "name": "Option 8 (PHY-RF, CPRI-like) — bent pipe",
        "onboard": ["O-RU"],
        "ground": ["O-DU", "O-CU", "5GC"],
        "payload_note": "RF front end only; no digital baseband to qualify for space",
    },
    "option7-2x": {
        "name": "Option 7-2x (intra-PHY, O-RAN fronthaul)",
        "onboard": ["O-RU", "low-PHY"],
        "ground": ["high-PHY", "O-DU", "O-CU", "5GC"],
        "payload_note": "beamforming weights applied on board; frequency-domain fronthaul",
    },
    "option2": {
        "name": "Option 2 (PDCP/RLC) — regenerative gNB-DU on board",
        "onboard": ["O-RU", "O-DU"],
        "ground": ["O-CU", "5GC"],
        "payload_note": "MAC and scheduler in orbit: HARQ loop closes on board",
    },
    "full-gnb": {
        "name": "Full gNB + local UPF on board",
        "onboard": ["O-RU", "O-DU", "O-CU", "UPF"],
        "ground": ["5GC control"],
        "payload_note": "inter-satellite routing becomes a transport problem, not a relay",
    },
}


def option8_fronthaul_bps(sample_rate_msps: float, bits_per_sample: int = 16,
                          antenna_ports: int = 2, carriers: int = 1,
                          line_coding: float = 10 / 8, control_overhead: float = 1.05):
    """Raw I/Q: 2 * bits * fs * ports * carriers, plus line coding and control."""
    return (2 * bits_per_sample * sample_rate_msps * 1e6 * antenna_ports
            * carriers * line_coding * control_overhead)


def option7_2x_fronthaul_bps(used_subcarriers: int, symbols_per_second: float,
                             bits_per_sample: int = 9, layers: int = 2,
                             overhead: float = 1.2):
    """Frequency-domain: only occupied resource elements, compressed."""
    return 2 * bits_per_sample * used_subcarriers * symbols_per_second * layers * overhead


def split_verdict(split: str, *, feeder_capacity_bps=None, **kw):
    s = SPLITS.get(split)
    if not s:
        return Unknown(f"unknown split {split}", tuple(SPLITS))
    if split == "option8":
        need = option8_fronthaul_bps(**{k: v for k, v in kw.items() if k in (
            "sample_rate_msps", "bits_per_sample", "antenna_ports", "carriers",
            "line_coding", "control_overhead")})
    elif split == "option7-2x":
        need = option7_2x_fronthaul_bps(**{k: v for k, v in kw.items() if k in (
            "used_subcarriers", "symbols_per_second", "bits_per_sample", "layers",
            "overhead")})
    else:
        need = kw.get("user_throughput_bps")
        if need is None:
            return Unknown(f"{split} feeder load is the user traffic itself",
                           ("user_throughput_bps",))
    out = dict(s)
    out["fronthaul_bps"] = need
    out["fronthaul_mbps"] = round(need / 1e6, 2)
    if feeder_capacity_bps is not None:
        out["feeder_capacity_mbps"] = round(feeder_capacity_bps / 1e6, 2)
        out["fits_feeder"] = need <= feeder_capacity_bps
        out["oversubscription"] = round(need / feeder_capacity_bps, 2)
    return out


def onboard_processing_load(split: str):
    """What has to survive radiation and a power budget if this split is chosen."""
    s = SPLITS.get(split)
    if not s:
        return Unknown(f"unknown split {split}", tuple(SPLITS))
    return {
        "onboard_functions": s["onboard"],
        "needs_space_qualified_baseband": any(f in s["onboard"] for f in ("O-DU", "low-PHY")),
        "harq_closes_onboard": "O-DU" in s["onboard"],
        "power_and_thermal": Unknown(
            "payload power and thermal budget are per-platform",
            ("bus power budget W", "radiator area", "duty cycle")),
    }
