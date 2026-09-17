# The state-of-the-art tier

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

Five tracks, each recorded at the rung it has actually reached. Promotion requires evidence in the tree; `ertabat sota --promote` refuses without it.

## Regenerative on-board processing with neuromorphic inference

**Rung** SPEC · **packet** SOTA-1

It displaces: ground-computed scheduling and beamforming.

**Computable here today**
- payload power and thermal budget from a declared bus budget
- the O-RAN split that puts the scheduler on board (ntn.oran option2)

**Not computable here**
- spiking-network accuracy under radiation-induced bit flips
- energy per inference for a specific part — no part is bound here

**The question that has to be answered first.** What does the scheduler do in the seconds after an SEU, and how is that different from what it does when the link is merely bad?

## Optical inter-satellite links and hybrid RF/optical switching

**Rung** SPEC · **packet** SOTA-2

It displaces: RF-only backhaul between satellites.

**Computable here today**
- geometric range and pointing rate between two orbits
- the RF fallback budget the optical link switches to

**Not computable here**
- acquisition and tracking loop performance
- cloud-blockage statistics for a ground site — needs a climatology

**The question that has to be answered first.** At what fade depth and over what horizon does the switch to RF pay for itself, given that the decision must be made before the fade?

## Cell-free massive MIMO across a satellite swarm

**Rung** SPEC · **packet** SOTA-3

It displaces: single-satellite spot beams with a handover every beam dwell.

**Computable here today**
- beam dwell and handover cadence that the scheme claims to remove
- phase-coherence budget implied by a stated clock stability

**Not computable here**
- joint precoding gain for a real constellation geometry
- inter-satellite ranging error budget

**The question that has to be answered first.** What clock and ranging error turns constructive interference at the user into destructive interference, and how often is that exceeded?

## Semantic and goal-oriented transmission

**Rung** SPEC · **packet** SOTA-4

It displaces: Shannon-limited bit transport.

**Computable here today**
- the bit-rate budget the semantic scheme is measured against

**Not computable here**
- reconstruction fidelity — which is the whole claim
- behaviour on inputs outside the shared model's training set

**The question that has to be answered first.** What is the failure mode when the two models drift apart, and how does the receiver know that it has happened rather than trusting a confident reconstruction?

## Quantum key distribution over the space segment

**Rung** SPEC · **packet** SOTA-5

It displaces: classical key exchange over the same link.

**Computable here today**
- the classical link budget the QKD channel rides beside

**Not computable here**
- secret key rate under loss and background counts
- detector dark-count and after-pulse behaviour in orbit

**The question that has to be answered first.** What is the key rate after finite-key correction at the loss this geometry actually gives, rather than at the loss in the abstract?
