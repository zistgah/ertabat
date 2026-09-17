"""The radio HAL: one interface, from a 20-dollar dongle to a flight SDR.

The same contract that lets the device element port across ESP32, Raspberry Pi
and an ASIC applies here across RTL-SDR, Pluto, USRP, a flight SDR and a
laboratory instrument. A driver implements the capabilities it really has and
DECLARES the rest. A declared absence is a passing driver; a fabricated sample
buffer is a failing one, and the test suite is built to tell them apart.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .. import Unknown


class NotFitted(Exception):
    """Raised when a driver is asked for a capability it has declared absent."""


@dataclass(frozen=True)
class Capability:
    name: str
    present: bool
    note: str = ""


@dataclass(frozen=True)
class DeviceSpec:
    """Everything another agent needs to write the driver without the hardware."""
    key: str
    display_name: str
    vendor: str
    tune_min_hz: float
    tune_max_hz: float
    max_sample_rate_sps: float
    adc_bits: int
    full_duplex: bool
    transmit: bool
    interface: str                       # usb2 | usb3 | ethernet | pcie | spi | uart
    driver_library: str                  # the host library a driver would bind to
    space_grade: str = "commercial"      # commercial | industrial | rad-tolerant | rad-hard
    notes: str = ""
    unknowns: tuple = field(default_factory=tuple)

    def covers(self, freq_hz: float) -> bool:
        return self.tune_min_hz <= freq_hz <= self.tune_max_hz


class RadioDevice(abc.ABC):
    """Minimum surface a radio must present to the rest of ertabat."""

    spec: DeviceSpec

    @abc.abstractmethod
    def capabilities(self) -> Sequence[Capability]:
        ...

    @abc.abstractmethod
    def open(self) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...

    @abc.abstractmethod
    def set_frequency(self, hz: float) -> None: ...

    @abc.abstractmethod
    def set_sample_rate(self, sps: float) -> None: ...

    @abc.abstractmethod
    def set_gain(self, db: float) -> None: ...

    @abc.abstractmethod
    def read_iq(self, n_samples: int) -> Iterable[complex]:
        """Return n complex samples, or raise NotFitted. NEVER synthesise."""

    @abc.abstractmethod
    def write_iq(self, samples) -> int: ...

    def has(self, name: str) -> bool:
        return any(c.name == name and c.present for c in self.capabilities())

    def self_describe(self) -> dict:
        return {
            "key": self.spec.key,
            "display_name": self.spec.display_name,
            "vendor": self.spec.vendor,
            "tune_hz": [self.spec.tune_min_hz, self.spec.tune_max_hz],
            "max_sample_rate_sps": self.spec.max_sample_rate_sps,
            "transmit": self.spec.transmit,
            "space_grade": self.spec.space_grade,
            "capabilities": {c.name: c.present for c in self.capabilities()},
            "unknowns": list(self.spec.unknowns),
            "implemented": self.__class__.__name__,
        }


def doppler_corrected_tuning(device: RadioDevice, nominal_hz: float, shift_hz: float):
    """Tune against the predicted shift, refusing when the tuner cannot reach it."""
    target = nominal_hz - shift_hz
    if not device.spec.covers(target):
        return Unknown(
            f"{device.spec.key} cannot tune {target/1e6:.3f} MHz",
            (f"range {device.spec.tune_min_hz/1e6:.1f}–{device.spec.tune_max_hz/1e6:.1f} MHz",
             "add a downconverter or choose another radio"))
    return target
