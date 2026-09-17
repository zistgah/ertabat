# AGENTS — how work enters this repository

Read `CONTRACT.md` and `CONTEXT.md` first, then run:

    bash ops/verify.sh
    bash ops/resume.sh && cat RESUME.md
    python3 -m ertabat.cli doctor
    python3 -m ertabat.cli dispatch

`doctor` tells you what is absent. `dispatch` gives you the packets that fill
those absences, each with the command that decides whether your work is done.

## The one rule that matters here

This repository would rather have a hole than a plausible number. If you cannot
compute something, return `ertabat.Unknown` naming what you need. Do not:

- fill a coefficient table from memory — cite the recommendation and record who
  populated it and when;
- return samples from a driver that has no hardware;
- price a part from a remembered figure;
- promote a SOTA track because the argument for it is convincing.

A contribution that adds an honest Unknown is accepted. A contribution that adds
a confident number without a source is reverted, and it is the only class of
change that is reverted without discussion.

## Routing

Packets carry capability labels: `needs:code`, `needs:proof`, `needs:testing`,
`needs:ontology`, `needs:visual`, `needs:legal`, `needs:human`. They do not carry
model names. Routing is a preference at dispatch time, not a property of the work.

## Before you open a pull request

    bash ops/verify.sh            # must print CONTRACT OK
    bash ops/selftest.sh          # must show the gates still biting
    python3 -m unittest discover -s tests

If you added a driver, show the conformance verdict:

    python3 -c "from ertabat.hal.conformance import check_driver, verdict; ..."

If you added a price provider, show that a 403, an empty result and a malformed
body each end as Unknown. Those three tests exist for every provider in the tree
and yours is not an exception.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

## Driving this through a cycler

`cyclers/ertabat.pni` is PANINI configuration: one packet in, one proof out. Run it
through the PANINI engine — any model, any vendor, or none — rather than restating
the brief in a chat window. The configuration IS the brief.

    mez cycler            # the desk mounts it; the desk does not own it
    panini check cyclers/ertabat.pni
