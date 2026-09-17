# Driving ertabat from the tools you already use

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

Every command takes `--json`, which is the whole integration story. ertabat computes
and declares; your tool simulates, draws or builds.

## MATLAB and Octave

    r = jsondecode(evalc("system('ertabat ntn --altitude-km 550 --gnss --json')"));
    kOffset = r.k_offset_slots;

Use it to size a Simulink NTN model rather than typing constants into it: the
k-offset, the HARQ process count and the PRACH residual come from the same
functions the test suite asserts on, so the model and the repository cannot
silently disagree. Octave reads the same JSON with `jsondecode`.

## Simulink

Build the channel from `ertabat pass --json`: maximum Doppler as the shift, the
Doppler rate as the ramp, the slant range as the delay. The two figures that
matter for a subcarrier-spacing choice are `max_doppler_hz` and
`max_doppler_rate_hz_s` — compare them to your numerology before choosing it.

## GNU Radio

A flowgraph's Doppler correction block wants a schedule, not a constant. Generate
one per pass and feed the sink; the HAL's `doppler_corrected_tuning` tells you
when the tuner cannot reach the corrected frequency, which is the case worth
catching before the pass rather than during it.

## srsRAN and OpenAirInterface

Packet NTN-1. `ertabat ntn` gives the values the stack has to accept; patch the
upstream constants with exact anchors, never by regenerating a file. Pin the
upstream commit in the patch header.

## KiCad and mechanical CAD

The BoM is the seam. Export the schematic BoM to CSV with columns
`ref,mpn,qty,manufacturer,description`, price it with `ertabat bom --out-csv`, and
feed the priced CSV back to the board's cost model. Antenna geometry and thermal
work belong in CAD; what ertabat supplies is the gain and the noise temperature the
budget assumed, so that the built antenna can be compared against the assumption.

## The device side

Rotator control, bias-tee switching and thermal sensing are device-control
problems and belong to `zasab`, the estate's embedded element. ertabat computes
where to point and what to tune; zasab moves the metal.
