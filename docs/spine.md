# The spine

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

The device element abstracts what a machine does to the world: sensors,
actuators, displays, behind a HAL, so one stack ports from an ESP32 to a
Raspberry Pi to an ASIC. This element abstracts what a machine says across a
distance. The two are deliberately the same shape, because the same failure
recurs in both: a layer that cannot do its job quietly pretends to, and every
layer above it reports success.

    ┌─────────────────────────────────────────────────────────────┐
    │  L5  orchestration    dispatch packets · conformance harness │
    │                       skills for agents · the acceptance     │
    │                       command that decides "done"            │
    ├─────────────────────────────────────────────────────────────┤
    │  L4  service          O-RAN functional split · feeder load   │
    │                       bent-pipe vs regenerative · handover   │
    ├─────────────────────────────────────────────────────────────┤
    │  L3  access           duplexing · HARQ · PRACH · k-offset    │
    │                       timing advance · beam dwell            │
    ├─────────────────────────────────────────────────────────────┤
    │  L2  link             modulation · required Eb/N0 · coding   │
    │                       symbol rate · spectral efficiency      │
    ├─────────────────────────────────────────────────────────────┤
    │  L1  channel          FSPL · G/T · C/N0 · margin             │
    │                       atmosphere · Doppler · slant range     │
    ├─────────────────────────────────────────────────────────────┤
    │  L0  radio HAL        RadioDevice · DeviceSpec · StubRadio   │
    │                       registry · doppler-corrected tuning    │
    └─────────────────────────────────────────────────────────────┘
      cross-cutting:  Unknown — refuses arithmetic, names what is missing
                      BoM     — every part, priced with its provenance
                      SOTA    — five tracks, each at the rung it reached

## The parallels, named

| device element | this element |
|---|---|
| `SensorSpec` / `ActuatorSpec` | `DeviceSpec` — tuning range, sample rate, transmit, space grade |
| HAL across ESP32 / Pi / ASIC | HAL across dongle / laboratory SDR / flight payload |
| honest stub for an unbuilt driver | `StubRadio` — refuses to produce samples |
| validation suite for contributed drivers | `hal.conformance` — mutation-tested against a liar |
| autoconf / automake | the same |
| CONTRACT · CONTEXT · Pages | the same |
| the orchestration stance | packets with acceptance commands, capability labels |

## The cross-cutting type

`Unknown` is the spine's spine. Every layer returns it rather than a default, and
it raises on arithmetic, so a missing atmospheric loss cannot become a zero that
makes a budget close. The pattern is worth stating plainly because it is what
makes multi-agent work safe here: a contributor who does not know something can
say so in the type system, and the layers above will carry that ignorance all the
way to the answer instead of laundering it.

## Where the device element takes over

Pointing a rotator, switching a bias tee, reading a temperature at the feed: all
device control. This element computes where to point, what to tune, and what the
budget assumed the antenna would deliver. The seam between them is a number and a
timestamp, not a shared library.
