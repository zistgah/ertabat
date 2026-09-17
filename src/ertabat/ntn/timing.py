"""Where terrestrial timing assumptions break in orbit, as arithmetic.

Every function here answers one of the failures named in the omissions list:
HARQ stalls, PRACH misses its window, the scheduler's k-offsets are too small.
The point of computing them is that a claim like "the timers need widening"
becomes a number a test can hold.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .. import Unknown


C_KM_S = 299792.458


def slot_duration_ms(numerology_mu: int) -> float:
    """NR slot length. 1 ms / 2^mu (15 kHz -> 1 ms, 30 kHz -> 0.5 ms)."""
    return 1.0 / (2 ** numerology_mu)


def one_way_delay_ms(distance_km: float) -> float:
    return 1000.0 * distance_km / C_KM_S


@dataclass
class DelayBudget:
    service_link_km: float
    feeder_link_km: float
    architecture: str
    one_way_ms: float
    rtt_ms: float
    differential_ms: float

    def __str__(self):
        return (f"{self.architecture}: one-way {self.one_way_ms:.2f} ms, "
                f"RTT {self.rtt_ms:.2f} ms, differential {self.differential_ms:.2f} ms")


def delay_budget(service_link_km, feeder_link_km=None, architecture="regenerative",
                 service_link_min_km=None):
    """RTT for the two architectures.

    regenerative: the gNB is on board, so the loop is UE <-> satellite.
    bent_pipe   : the gNB is on the ground, so every ack also crosses the
                  feeder link twice — this is the term that surprises people.
    """
    a = architecture.replace("-", "_").lower()
    if a not in ("regenerative", "bent_pipe"):
        return Unknown(f"unknown architecture {architecture}",
                       ("regenerative", "bent_pipe"))
    if a == "bent_pipe" and feeder_link_km is None:
        return Unknown("bent-pipe RTT", ("feeder_link_km",))
    one = one_way_delay_ms(service_link_km) + \
        (one_way_delay_ms(feeder_link_km) if a == "bent_pipe" else 0.0)
    dmin = service_link_min_km if service_link_min_km is not None else service_link_km
    diff = one_way_delay_ms(service_link_km) - one_way_delay_ms(dmin)
    return DelayBudget(service_link_km, feeder_link_km or 0.0, a, one, 2 * one, diff)


def harq_processes_needed(rtt_ms: float, tti_ms: float) -> int:
    """How many parallel processes keep the pipe full across this RTT."""
    return max(1, math.ceil(rtt_ms / tti_ms))


def harq_verdict(rtt_ms: float, tti_ms: float, available_processes: int = 16):
    need = harq_processes_needed(rtt_ms, tti_ms)
    ok = need <= available_processes
    return {
        "processes_needed": need,
        "processes_available": available_processes,
        "stop_and_wait_throughput_fraction": round(tti_ms * available_processes / max(rtt_ms, tti_ms), 4)
        if rtt_ms > 0 else 1.0,
        "feasible_with_feedback": ok,
        "remedy": None if ok else
        "widen the HARQ RTT (3GPP NTN k_offset), raise the process count, or "
        "disable HARQ feedback for this bearer and lean on RLC ARQ",
    }


def k_offset_slots(rtt_ms: float, numerology_mu: int = 1) -> int:
    """K_offset: the scheduling offset that has to cover the whole RTT."""
    return math.ceil(rtt_ms / slot_duration_ms(numerology_mu))


def prach_verdict(differential_delay_ms: float, preamble_format: str, cp_length_us: float,
                  gnss_precompensation: bool = True, residual_error_us: float = 10.0):
    """Random access succeeds only if the residual delay fits the cyclic prefix."""
    residual_us = residual_error_us if gnss_precompensation else differential_delay_ms * 1000.0
    return {
        "preamble_format": preamble_format,
        "cyclic_prefix_us": cp_length_us,
        "residual_delay_us": round(residual_us, 3),
        "fits": residual_us <= cp_length_us,
        "remedy": None if residual_us <= cp_length_us else
        "pre-compensate timing from GNSS and broadcast the common TA (3GPP "
        "Rel-17 NTN), or choose a long-CP preamble format",
    }


def timing_advance_ms(distance_km: float, common_ta_ms: float = 0.0) -> float:
    return 2 * one_way_delay_ms(distance_km) + common_ta_ms


def handover_cadence_s(beam_dwell_s: float, signalling_ms_per_handover: float = 50.0):
    return {
        "handover_every_s": round(beam_dwell_s, 2),
        "handovers_per_hour": round(3600.0 / beam_dwell_s, 1),
        "signalling_duty_cycle": round(signalling_ms_per_handover / (beam_dwell_s * 1000.0), 5),
    }
