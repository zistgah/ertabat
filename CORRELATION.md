# CORRELATION — what ertabat shares, and with whom

Declared, not inferred. Every entry is in `descriptor.json` and is checked by
`dhancha/tools/spine_correlate.py`; a shared primitive must be declared from both ends.

| with | kind | what is actually shared |
|---|---|---|
| `zasab` | shares_primitive | the dhancha shape: one interface, one registry, N ports, a conformance harness. A radio is reached the same way a sensor is. **Nothing else** — the workflows differ completely, and D9 forbids borrowing the other's vocabulary. |
| `chakra` | consumes | time and pass geometry. The observatory kernel already computes ephemerides; this domain asks it rather than growing a second almanac. |
| `transeg` | supplies | the carrier an embodiment's telemetry crosses. transeg owns the staged consent model; ertabat owns the link. |
| `pedler` | consumes | propagation treated as an event-hypergraph question rather than a closed-form table. |
| `atlasviz` | supplies | spectra and link budgets as data to draw. atlasviz draws; it does not measure. |
| `fakir` | same_lattice_point | ISIC J61 x ISCO 2153 x ISCED 0714, AGI layers L0-L5. |
| `dhancha` | consumes | the ten invariants. |
| `mez` | mounts_in | a panel on the desk. Sovereign — it runs without the desk, and the desk runs without it. |

## The one that matters

`zasab` and `ertabat` share a **primitive**, not an **architecture**. The registry-and-ports
shape is an implementation economy. Device control and communication engineering have
different purposes, contracts, state models, failure modes and evidence requirements, and
each authors its own. Inferring a shared architecture from shared code is the error
recorded against this estate before, and D9 exists to make it fail a test rather than a review.
