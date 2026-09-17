# ertabat · ارتباط

The link. A communication-engineering spine for space and non-terrestrial radio,
built so that several agents can work on it at once without any of them being
able to quietly invent a number.

    python3 -m ertabat.cli doctor        # what is present, what is declared absent
    python3 -m ertabat.cli dispatch      # the work packets, each with its own test

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

## What it computes

    ertabat pass  --altitude-km 550 --freq-mhz 437 --beamwidth-deg 40
    ertabat link  --tx-power-dbw 0 --tx-gain-dbi 2 --altitude-km 550 --freq-mhz 437 \
               --rx-gain-dbi 18 --system-noise-temp-k 250 --data-rate-bps 9600 \
               --modulation QPSK --atmospheric-loss-db 1.0
    ertabat ntn   --altitude-km 550 --elevation-deg 10 --gnss
    ertabat oran  --split option8 --sample-rate-msps 30.72 --antenna-ports 2 \
               --feeder-capacity-bps 500e6
    ertabat hal   --freq-mhz 437
    ertabat bom   bom/ground-station-sdr.csv --currency INR

At 550 km and 437 MHz the Doppler shift is ±10.2 kHz and swings at 134 Hz/s; a
ten-degree pass lasts about eight and a half minutes; the round trip is 12.1 ms,
which needs 25 HARQ processes where the standard provides 16, and a k-offset of
25 slots at 30 kHz spacing; the TDD guard period would have to be 4.2 ms, so the
link is FDD; and a 400 km spot beam hands over every minute. Those are outputs,
not assertions — run them.

## Bill of materials, priced online

`ertabat bom` reads a CSV of parts and prices it against distributor APIs:

| provider | key | note |
|---|---|---|
| local price book | none | the keyless path — paste the quotations you hold |
| Nexar / Octopart | `ERTABAT_NEXAR_TOKEN_FILE` | aggregates most distributors |
| Mouser | `ERTABAT_MOUSER_KEY_FILE` | |
| element14 / Farnell | `ERTABAT_ELEMENT14_KEY_FILE` | INR pricing via the India storefront |
| DigiKey | `ERTABAT_DIGIKEY_TOKEN_FILE` | also needs an OAuth2 client id |
| LCSC | — | declared unavailable: no public catalogue API |

Keys are paths to files, never flags. Results are cached beside the BoM. An
unpriced line stays unpriced, and a BoM quoted in two currencies has no total
until an exchange-rate file naming its source and date is supplied.

    ertabat bom bom/cubesat-1u-lband.csv --price-book bom/prices.csv \
             --fx bom/fx.json --out-md BOM.md --out-csv BOM.csv

## Why the tables are empty

`data/itu_p838.json` and `data/itu_p676.json` ship with no rows, so every rain
and gas figure comes back Unknown. That is deliberate: those coefficients are
published tables, and a table typed from memory is the kind of plausible number
this repository exists to keep out. Populate them from the recommendation, record
who did it and when, and four skipped tests start running.

## Layout

    src/ertabat/link      budget · modulation · geometry · atmosphere
    src/ertabat/ntn       timing · duplex · oran
    src/ertabat/hal       base · devices · stub · registry · conformance
    src/ertabat/bom       model · providers · lookup · report
    src/ertabat/sota      the five state-of-the-art tracks at their real rung
    skills/            how another agent adds a driver, a provider, a block
    ops/               verify · resume · selftest

## Verifying it

    bash ops/verify.sh      # ten contract checks
    bash ops/selftest.sh    # runs the suite AND proves the gates still refuse
