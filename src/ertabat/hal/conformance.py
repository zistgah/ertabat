"""Does a contributed driver tell the truth?

This is the harness the estate's device element earned: work arrives from other
agents, and the question is never "did it run" but "did it say what it did".
A driver passes by refusing loudly when it has nothing, and fails by returning a
buffer that looks like a signal.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

from dataclasses import dataclass

from .base import Capability, DeviceSpec, NotFitted, RadioDevice


@dataclass
class Finding:
    check: str
    passed: bool
    detail: str


def check_driver(dev, *, hardware_present: bool = False):
    """Run the honesty checks. With no hardware attached, a driver must refuse."""
    f = []

    f.append(Finding("implements RadioDevice", isinstance(dev, RadioDevice),
                     type(dev).__name__))
    f.append(Finding("carries a DeviceSpec", isinstance(getattr(dev, "spec", None), DeviceSpec),
                     str(getattr(dev, "spec", None))[:60]))

    caps = list(dev.capabilities()) if hasattr(dev, "capabilities") else []
    f.append(Finding("declares capabilities",
                     bool(caps) and all(isinstance(c, Capability) for c in caps),
                     f"{len(caps)} declared"))

    claims_rx = any(c.name == "receive" and c.present for c in caps)
    if not hardware_present:
        try:
            got = dev.read_iq(64)
            n = len(list(got))
            f.append(Finding("refuses to invent samples", False,
                             f"returned {n} samples with no hardware bound — "
                             "this is the failure the harness exists to catch"))
        except NotFitted as e:
            f.append(Finding("refuses to invent samples", True, str(e)[:70]))
        except Exception as e:
            f.append(Finding("refuses to invent samples", False,
                             f"raised {type(e).__name__} instead of NotFitted: {e}"))
        f.append(Finding("does not claim receive without hardware", not claims_rx,
                         "capability 'receive' is declared present" if claims_rx else "ok"))

    try:
        d = dev.self_describe()
        ok = isinstance(d, dict) and {"key", "capabilities"} <= set(d)
        f.append(Finding("self-describes", ok, ", ".join(sorted(d)) if ok else str(d)[:60]))
    except Exception as e:
        f.append(Finding("self-describes", False, f"{type(e).__name__}: {e}"))

    try:
        dev.set_frequency(dev.spec.tune_max_hz * 10)
        f.append(Finding("rejects an out-of-range tune", False,
                         "accepted a frequency ten times its published maximum"))
    except ValueError:
        f.append(Finding("rejects an out-of-range tune", True, "ValueError, correctly"))
    except Exception as e:
        f.append(Finding("rejects an out-of-range tune", False,
                         f"raised {type(e).__name__} rather than ValueError"))
    return f


def verdict(findings):
    bad = [f for f in findings if not f.passed]
    return {"checks": len(findings), "failed": len(bad),
            "passed": not bad,
            "failures": [f"{f.check}: {f.detail}" for f in bad]}
