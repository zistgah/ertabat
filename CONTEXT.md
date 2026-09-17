# CONTEXT — ertabat (ارتباط)

**ertabat** is the communication element of the Zistgah estate: the link, as
`zasab` (اعصاب) is the nerve. Where zasab abstracts sensors, actuators and
displays so that one stack ports across ESP32, Raspberry Pi and an ASIC, ertabat
abstracts the radio so that one stack reasons identically about a twenty-dollar
dongle, a laboratory SDR and a flight payload — and about the link that runs
between them.

## What it is for

Communication engineering as it is taught assumes a fixed base station, a slow
user and mains power. Put the base station in a 7.5 km/s orbit and the
assumptions fail one at a time: the Doppler shift exceeds the subcarrier
spacing, the TDD guard period cannot cover the propagation differential, the
HARQ timers expire before an acknowledgement can physically arrive, and random
access fails because the preamble's cyclic prefix was sized for a cell a few
kilometres across.

Those are usually discussed in prose. Here each is a function that returns a
number, so a claim about them can be checked rather than agreed with.

## The shape

    link/        budget · modulation · geometry · atmosphere
    ntn/         timing · duplex · oran
    hal/         base · devices · stub · registry · conformance
    bom/         model · providers · lookup · report
    sota/        the five bleeding-edge tracks, at their real rung
    dispatch     work packets with acceptance tests

## What is deliberately absent

The ITU-R coefficient tables ship empty. SGP4 is not vendored. No radio driver
is bound. Every one of those absences is declared by `ertabat doctor` and carries a
work packet. The repository is more useful with holes that announce themselves
than with plausible numbers of unknown origin.

## Relationship to the rest of the estate

- **zasab** — the rotator controller, the bias-tee switching and the thermal
  sensing of a ground station are device-control problems and belong there; ertabat
  computes the pointing and the tuning that zasab acts on.
- **governance** — contract, zops, seal and gate.
- **misty-doi** — the publication path, when and if he mints it.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
