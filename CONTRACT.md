# CONTRACT — ertabat

This is a thin overlay on the master contract at `zistgah/governance`. It ADDS
constraints and relaxes none. Where the two differ, the master wins.

Sole author: Abhishek Choudhary. Affiliation: AyeAI. No other affiliation is
credited on any output of this repository.

© 1993–2026 Abhishek Choudhary. All rights reserved.

## R1 — a missing number is Unknown, never zero

Every function that cannot compute its result returns `ertabat.Unknown` naming what
is missing. `Unknown` refuses arithmetic, so a hole cannot be summed over. This
is enforced: `ops/verify.sh` R4 fails the repo if the atmosphere module returns a
figure while its coefficient table is empty.

Earned by the ordinary way a link budget lies: the atmospheric term is left out,
the margin comes out positive, and the paper says the link closes.

## R2 — a driver that cannot receive says so

An unbound radio raises `NotFitted`. It does not return zeros, noise, or a
replayed capture presented as live. `ops/verify.sh` R5 asserts the refusal, and
R6 asserts that the conformance harness still CATCHES a driver that fabricates —
the harness is mutation-tested against a deliberate liar in `tests/test_hal.py`.

## R3 — a price carries its source and its timestamp

No quote enters the tree without `source` and `retrieved_utc`. A row in the local
price book without them is refused. An unpriced line is reported as unpriced and
blocks the combined total: a total over the priced subset would read as the cost
of the build.

## R4 — currency is converted only against a declared rate

A mixed-currency BoM has no single total until an exchange-rate file naming its
source and its date is supplied. Absent that, the subtotals stand and the total
is Unknown.

## R5 — credentials are read from files, never from flags

Every provider key is `<PROVIDER>_KEY_FILE` or `<PROVIDER>_TOKEN_FILE` holding a
path. `ops/verify.sh` R8 fails the repo if any argument parser grows a key flag.

## R6 — a rung is claimed with evidence

The SOTA tracks sit at SPEC. Promotion to MODEL, SIMULATED, BENCH or FLIGHT
requires evidence in the tree, and `ertabat sota --promote` refuses without it.

## R7 — a packet is done when its test passes

Work is dispatched as packets carrying inputs, interface and an acceptance
command. A packet is complete when that command passes. Labels are capabilities
(`needs:code`, `needs:proof`, `needs:testing`, `needs:ontology`) and never model
names: which agent takes the work is a dispatch decision by the human.

## R8 — contributed work is verified before it is believed

Anything arriving from another agent runs `ops/verify.sh` and the conformance
harness before it is merged. A passing suite is not evidence until the suite has
been shown to fail on a broken input.

Reconstruct faithfully. Critique with evidence, not tone. Maintain contract and
context.
