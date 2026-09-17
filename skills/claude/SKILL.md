---
name: ertabat
description: Use when working on ertabat — the communication-engineering spine for space and non-terrestrial radio. Covers link budgets, Doppler and pass geometry, NTN timing (HARQ, PRACH, k-offset, duplexing), O-RAN functional splits, the radio HAL and its conformance harness, the SOTA track ladder, and online BoM price lookup. Trigger on link budget, Doppler, CubeSat, ground station, SDR, 5G NTN, O-RAN split, spot beam handover, or pricing a bill of materials.
---

# Working on ertabat

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

## Before anything

    bash ops/verify.sh && bash ops/resume.sh && cat RESUME.md
    python3 -m ertabat.cli doctor

`doctor` is the state of the world: which tables are populated, which radios are
bound, which price providers are configured. Everything it calls absent is
absent — do not work around it, and do not fill it from memory.

## The invariant

`ertabat.Unknown` is a value, and it refuses arithmetic. If you find yourself
wanting a default so that a computation can proceed, that is the moment the
repository is telling you something: the input is missing and the result does not
exist yet. Return `Unknown(reason, needs)`.

Three failures this suite is built to catch, because each has happened somewhere:

1. an atmospheric term silently zero, so the link "closes";
2. a driver returning a buffer of zeros, so the receiver "works";
3. a total over the priced half of a BoM, read as the cost of the build.

## Where things live

| you want | it is in |
|---|---|
| EIRP, FSPL, G/T, C/N0, Eb/N0, margin | `link/budget.py` |
| required Eb/N0 for a modulation | `link/modulation.py` — derived by inverting Q(), not tabulated |
| Doppler, pass duration, beam dwell | `link/geometry.py` |
| rain, gas, scintillation | `link/atmosphere.py` — table-driven, tables ship empty |
| RTT, HARQ, k-offset, PRACH, handover | `ntn/timing.py` |
| TDD versus FDD | `ntn/duplex.py` |
| split options and feeder load | `ntn/oran.py` |
| radios and drivers | `hal/` |
| prices | `bom/` |

## Adding to it

New physics goes behind a function that can return Unknown. New hardware goes in
`hal/devices.py` as a `DeviceSpec` with an `unknowns` tuple for every figure the
datasheet does not give. New distributors go in `bom/providers.py` as a
`PriceProvider` subclass with the three failure-path tests.

## What not to do

Do not vendor an ITU table from memory. Do not add a `--api-key` flag. Do not
promote a SOTA track. Do not widen a test to make a contribution pass; the tests
are the contract with the other agents working on this tree.
