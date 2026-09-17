#!/usr/bin/env bash
# Generate RESUME.md — live state, never hand-edited.
# © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src:${PYTHONPATH:-}"
U="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
H="$(git rev-parse --short HEAD 2>/dev/null || echo 'no commit yet')"
B="$(git symbolic-ref --short HEAD 2>/dev/null || echo main)"
V="$(python3 -c 'import ertabat;print(ertabat.__version__)' 2>/dev/null || echo '?')"
{
echo "# RESUME · ertabat"
echo
echo "generated $U · HEAD $H on $B · version $V"
echo
echo "## Feature census — does this already exist?"
echo '```'
for f in link_budget slant_range_km required_ebn0_db max_doppler_hz pass_duration_s \
         beam_dwell_s delay_budget harq_verdict k_offset_slots prach_verdict \
         duplex_verdict split_verdict check_driver PriceService LocalPriceBook \
         NexarProvider MouserProvider Element14Provider load_fx PACKETS TRACKS; do
  n=$(grep -RIl --include="*.py" -E "(def|class) +$f|^$f *=" src 2>/dev/null | head -1)
  printf '%-22s %s\n' "$f" "${n:-ABSENT}"
done
echo '```'
echo
echo "## Declared absences (this is the work queue)"
python3 -m ertabat.cli doctor 2>/dev/null | sed 's/^/    /'
echo
echo "## Radios"
python3 -m ertabat.cli hal 2>/dev/null | sed 's/^/    /'
echo
echo "## SOTA rungs"
python3 -m ertabat.cli sota 2>/dev/null | sed 's/^/    /'
echo
echo "## Contract"
bash ops/verify.sh 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | sed 's/^/    /'
echo
echo "## Last commits"
git --no-pager log --oneline -5 2>/dev/null | sed 's/^/    /' || echo "    (none)"
echo
echo "© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI."
} > RESUME.md
echo "wrote RESUME.md"
