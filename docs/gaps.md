# The omissions, as things that can fail

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

Textbook communication engineering assumes a stationary base station, a slow
user and mains power. Each assumption fails in orbit in a specific way, and each
failure is a function here rather than a paragraph.

| assumption | what happens in orbit | where it is computed | the number at 550 km |
|---|---|---|---|
| carrier frequency is stable | ±10.2 kHz at 437 MHz, 280 kHz at 12 GHz, swinging at 134 Hz/s | `geometry.max_doppler_hz`, `max_doppler_rate_hz_s` | exceeds 15 kHz subcarrier spacing above L-band |
| propagation delay is negligible | 6.1 ms one way at ten degrees | `timing.delay_budget` | RTT 12.1 ms |
| TDD guard covers the cell | guard would need 4.2 ms | `duplex.duplex_verdict` | 71 µs buys a 10.7 km radius, so FDD |
| HARQ acknowledges within the timer | 25 processes needed | `timing.harq_verdict` | 16 available, so widen or drop feedback |
| PRACH preamble reaches within its CP | 4.2 ms differential against a 103 µs CP | `timing.prach_verdict` | needs GNSS pre-compensation and common TA |
| the user moves, the tower does not | the footprint moves at 7 km/s | `geometry.beam_dwell_s` | handover every 61 s for a 40° beam |
| fronthaul is a cable | Option 8 is 2.6 Gbps for 20 MHz on two ports | `oran.option8_fronthaul_bps` | five times a 500 Mbps feeder |
| the atmosphere is a small constant | rain and gas dominate above 10 GHz | `atmosphere` | Unknown until the ITU tables are populated |

Run the last column rather than trusting it:

    ertabat pass --altitude-km 550 --freq-mhz 437 --beamwidth-deg 40
    ertabat ntn  --altitude-km 550 --elevation-deg 10
    ertabat oran --split option8 --sample-rate-msps 30.72 --antenna-ports 2 \
              --feeder-capacity-bps 500e6

Changing an assumption changes the table. That is the point of it being code.
