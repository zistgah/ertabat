# Work packets

Each packet is complete: inputs, interface, and the command that decides whether it is done. Take one, finish it, prove it.

## ATM-1 — Populate ITU-R P.838 rain coefficients

**Labels** needs:proof · needs:code

Every Ku and Ka budget in this repo returns Unknown until the k/alpha table exists. This single file unblocks the whole high-band tier.

**Inputs**
- ITU-R P.838-3 tables 1 and 2

**Interface** data/itu_p838.json per ertabat.link.atmosphere.SCHEMA_P838, with populated_by and retrieved_utc filled in

**Accepted when** `python3 -m pytest tests/test_atmosphere.py -k populated  (skips while the table is absent, runs and must pass once present)`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted

## ATM-2 — Populate ITU-R P.676 gaseous absorption coefficients

**Labels** needs:proof · needs:code

Gaseous absorption is the term that is always omitted and always there; above 10 GHz it decides whether the link closes.

**Inputs**
- ITU-R P.676 line-by-line or approximate method

**Interface** data/itu_p676.json per SCHEMA_P676

**Accepted when** `python3 -m pytest tests/test_atmosphere.py -k gaseous`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted

## ATM-3 — Implement P.618 tropospheric scintillation

**Labels** needs:code · needs:proof

Scintillation is what actually breaks high-order QAM on a low elevation pass, and the module currently declares it unimplemented.

**Inputs**
- ITU-R P.618 section 2.4.1
- N_wet for the site from P.453

**Interface** ertabat.link.atmosphere.scintillation_fade_db returns a number when n_wet is supplied and Unknown when it is not

**Accepted when** `python3 -m pytest tests/test_atmosphere.py -k scintillation`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted

## DRV-1 — Bind a real RTL-SDR driver

**Labels** needs:code · needs:testing

The first real receiver in the HAL: it makes every downstream claim testable against a captured signal instead of a stub.

**Inputs**
- librtlsdr
- skills/agents/driver-authoring.md

**Interface** ertabat.hal.registry.register('rtlsdr-v3', factory) with a class implementing RadioDevice; read_iq returns real samples or raises

**Accepted when** `python3 -m pytest tests/test_hal.py  (the honesty tests must still pass for every unbound device)`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted

## DRV-2 — Bind a Pluto or USRP driver with GPSDO timing

**Labels** needs:code · needs:testing

Timing discipline is the precondition for any NTN experiment; a free-running oscillator cannot hold a PRACH window.

**Inputs**
- libiio or UHD
- a 10 MHz reference

**Interface** As DRV-1, plus a reference_locked() capability that is False when the reference is absent

**Accepted when** `python3 -m pytest tests/test_hal.py -k reference`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted

## BOM-1 — Add a distributor price provider

**Labels** needs:code

Coverage of Indian and Chinese supply is thin, which is where these builds are actually sourced.

**Inputs**
- distributor API documentation
- skills/agents/provider-authoring.md

**Interface** A PriceProvider subclass in ertabat/bom/providers.py registered in REGISTRY; key read by file path only

**Accepted when** `python3 -m pytest tests/test_bom.py  (including the failure-path tests: a 403, an empty result and a malformed body all end Unknown)`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted

## NTN-1 — Widen the srsRAN or OpenAirInterface HARQ and RACH timers

**Labels** needs:code · needs:testing

ertabat computes the k_offset and the RACH window a given orbit needs; the stacks have to be patched to accept them.

**Inputs**
- srsRAN or OAI source
- ertabat ntn timing output for the target orbit

**Interface** A patch series against the upstream tree with the computed values, no whole-file regeneration, exact anchors

**Accepted when** `ertabat ntn --altitude <km> --elevation <deg> agrees with the patched constants; the patch applies cleanly to a pinned upstream commit`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted

## SOTA-1 — Neuromorphic OBP: fault behaviour under SEU

**Labels** needs:ontology · needs:proof

The track is at SPEC and cannot be promoted without this.

**Inputs**
- a bound part with a TID and SEU rating

**Interface** A written model of scheduler behaviour after an upset, and the measurement that would distinguish it from a bad link

**Accepted when** `ertabat sota --promote obp-neuromorphic --to MODEL --evidence <path> must be accepted, which requires the evidence to exist`

**Not acceptable**
- inventing a numeric constant that is not derived or cited
- returning a value where the module currently returns Unknown, without naming the source of the value
- a driver that synthesises samples instead of raising NotFitted
