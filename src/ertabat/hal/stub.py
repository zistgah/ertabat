"""The honest stub: the default driver for hardware nobody has wired up yet.

It answers every question about the device truthfully from its spec, and it
raises the moment it is asked to produce data it does not have. That is the
whole point — a stub that returns zeros or noise looks like a working receiver
to every layer above it, and a link that "closes" against it proves nothing.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

from typing import Iterable, Sequence

from .base import Capability, DeviceSpec, NotFitted, RadioDevice


class StubRadio(RadioDevice):
    kind = "stub"

    def __init__(self, spec: DeviceSpec):
        self.spec = spec
        self._open = False
        self._freq = None
        self._rate = None
        self._gain = None

    def capabilities(self) -> Sequence[Capability]:
        return (
            Capability("tune", False, "declared: no hardware bound"),
            Capability("receive", False, "declared: no samples exist"),
            Capability("transmit", False, "declared: no hardware bound"),
            Capability("self_describe", True, "spec is real even when the radio is not"),
        )

    def open(self) -> None:
        self._open = True            # opening a stub is honest: it opens nothing

    def close(self) -> None:
        self._open = False

    def set_frequency(self, hz: float) -> None:
        if not self.spec.covers(hz):
            raise ValueError(f"{hz} Hz outside {self.spec.key} tuning range")
        self._freq = hz              # recorded, not applied

    def set_sample_rate(self, sps: float) -> None:
        if sps > self.spec.max_sample_rate_sps:
            raise ValueError(f"{sps} sps above {self.spec.key} maximum")
        self._rate = sps

    def set_gain(self, db: float) -> None:
        self._gain = db

    def read_iq(self, n_samples: int) -> Iterable[complex]:
        raise NotFitted(
            f"{self.spec.key}: no driver bound, so there are no samples. "
            "A stub does not invent a signal — bind a real driver "
            "(see skills/agents/driver-authoring.md) or use a recorded capture.")

    def write_iq(self, samples) -> int:
        raise NotFitted(f"{self.spec.key}: no driver bound, nothing was transmitted.")

    def state(self) -> dict:
        return {"open": self._open, "frequency_hz": self._freq,
                "sample_rate_sps": self._rate, "gain_db": self._gain,
                "note": "recorded settings; nothing was applied to hardware"}
