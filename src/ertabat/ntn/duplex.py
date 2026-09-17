"""TDD or FDD, decided by the guard period rather than by preference.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

from .. import Unknown

C_KM_S = 299792.458


def max_cell_radius_km(guard_period_us: float) -> float:
    """A TDD guard period buys a radius: R = c * GP / 2."""
    return C_KM_S * (guard_period_us * 1e-6) / 2.0


def required_guard_period_us(round_trip_differential_ms: float) -> float:
    return round_trip_differential_ms * 1000.0


def duplex_verdict(differential_delay_ms: float, guard_period_us: float,
                   symbol_duration_us: float = None):
    need = required_guard_period_us(differential_delay_ms)
    feasible = guard_period_us >= need
    out = {
        "guard_period_us": guard_period_us,
        "guard_period_needed_us": round(need, 2),
        "tdd_cell_radius_km": round(max_cell_radius_km(guard_period_us), 1),
        "tdd_feasible": feasible,
        "recommendation": "TDD" if feasible else "FDD",
        "why": ("the guard period already covers the differential delay"
                if feasible else
                "the guard period would have to swallow the whole differential "
                "propagation delay; at that length it costs more symbols than "
                "the slot contains, so the uplink and downlink take separate "
                "spectrum instead"),
    }
    if symbol_duration_us:
        out["guard_symbols_needed"] = round(need / symbol_duration_us, 1)
    return out


def fdd_duplex_spacing_note(band: str):
    return Unknown(f"duplex spacing for {band} is a regulatory allocation, "
                   "not a computed value", ("3GPP TS 38.101-5 band table",
                                            "or the national allocation"))
