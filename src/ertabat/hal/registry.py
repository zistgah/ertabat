"""Driver registry: bind real drivers where they exist, stub where they do not.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

from .. import Unknown
from .base import RadioDevice
from .devices import SPECS
from .stub import StubRadio

_DRIVERS = {}


def register(key: str, factory):
    """Bind a driver factory to a device key. Contributed drivers land here."""
    if key not in SPECS:
        raise KeyError(f"no spec for {key} — add the DeviceSpec first")
    _DRIVERS[key] = factory
    return factory


def open_device(key: str, **kw):
    if key not in SPECS:
        return Unknown(f"no device spec named {key}", tuple(sorted(SPECS)))
    factory = _DRIVERS.get(key)
    dev = factory(SPECS[key], **kw) if factory else StubRadio(SPECS[key])
    if not isinstance(dev, RadioDevice):
        raise TypeError(f"driver for {key} does not implement RadioDevice")
    return dev


def census():
    return {k: ("driver" if k in _DRIVERS else "stub") for k in sorted(SPECS)}


def bound_drivers():
    return sorted(_DRIVERS)
