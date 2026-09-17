#!/usr/bin/env bash
# Contract verification for ertabat. Exits non-zero when the repo breaks its word.
# © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
set -uo pipefail
cd "$(dirname "$0")/.."
J=0; [ "${1:-}" = "--json" ] && J=1
F=0; declare -a ROWS
chk(){ local id="$1" d="$2"; shift 2
  if "$@" >/dev/null 2>&1; then ROWS+=("PASS|$id|$d")
  else ROWS+=("FAIL|$id|$d"); F=$((F+1)); fi; }

chk R1-copyright "every source file carries the copyright line" bash -c '
  m=0
  for f in $(find src ops tests -type f \( -name "*.py" -o -name "*.sh" \) \
             -not -path "*/__pycache__/*"); do
    grep -q "Abhishek Choudhary" "$f" || { echo "$f"; m=1; }
  done; [ $m -eq 0 ]'
# The check distinguishes a CLAIM from a PROHIBITION: the clause that forbids a
# string necessarily contains it, and flagging the rule as a breach of itself is
# a failure this estate has already paid for once.
chk R2-affiliation "no affiliation other than AyeAI is claimed" bash -c '
  hits=$(grep -RIn --exclude-dir=.git --exclude=verify.sh -E "Independent Researcher" . \
         | grep -viE "never|not |forbidden|prohibit|must not|no affiliation" || true)
  [ -z "$hits" ] || { echo "$hits"; false; }'
chk R3-suite "the unit suite passes" bash -c 'PYTHONPATH=src python3 -m unittest discover -s tests -q'
chk R4-no-fabrication "no module invents a number where it should declare" bash -c '
  PYTHONPATH=src python3 - <<PY
from ertabat.link import atmosphere as a
from ertabat import Unknown
import sys, os, json
p = "data/itu_p838.json"
rows = False
if os.path.exists(p):
    with open(p) as fh: rows = bool(json.load(fh).get("rows"))
if not rows:
    r = a.specific_rain_attenuation_db_km(12, 30, "horizontal")
    sys.exit(0 if isinstance(r, Unknown) else 1)
sys.exit(0)
PY'
chk R5-stub-honesty "an unbound radio refuses to produce samples" bash -c '
  PYTHONPATH=src python3 - <<PY
from ertabat.hal.registry import open_device
from ertabat.hal.base import NotFitted
import sys
d = open_device("rtlsdr-v3"); d.open()
try:
    d.read_iq(8); sys.exit(1)
except NotFitted:
    sys.exit(0)
PY'
chk R6-conformance-bites "the conformance harness catches a fabricating driver" bash -c '
  PYTHONPATH=src python3 -m unittest tests.test_hal.TestConformanceBites -q'
chk R7-price-provenance "no price is carried without a source and a timestamp" bash -c '
  PYTHONPATH=src python3 -m unittest tests.test_bom.TestLocalPriceBook -q'
chk R8-tokens-by-path "no API key is read from a command-line flag" bash -c '
  ! grep -RIn --include="*.py" -E "add_argument\(.*--(api-)?key" src | grep -q .'
chk R9-packets "every dispatch packet carries an acceptance test" bash -c '
  PYTHONPATH=src python3 -c "
from ertabat.dispatch import PACKETS
import sys
sys.exit(0 if all(p.acceptance.strip() for p in PACKETS) else 1)"'
chk R10-sota-rungs "no SOTA track claims a rung above SPEC without evidence" bash -c '
  PYTHONPATH=src python3 -c "
from ertabat.sota.registry import TRACKS, LADDER
import os, sys
bad=[k for k,t in TRACKS.items() if LADDER.index(t.status)>0]
sys.exit(1 if bad else 0)"'

if [ "$J" = "1" ]; then
  printf '{"failed":%s,"checks":[' "$F"
  s=""; for r in "${ROWS[@]}"; do IFS='|' read -r a b c <<<"$r"
    printf '%s{"id":"%s","status":"%s","desc":"%s"}' "$s" "$b" "$a" "$c"; s=","; done
  printf ']}\n'
else
  echo; for r in "${ROWS[@]}"; do IFS='|' read -r a b c <<<"$r"
    if [ "$a" = PASS ]; then printf '  \033[32m✓\033[0m %-22s %s\n' "$b" "$c"
    else printf '  \033[31m✗\033[0m %-22s %s\n' "$b" "$c"; fi; done
  echo; [ "$F" -eq 0 ] && echo "  CONTRACT OK" || echo "  CONTRACT VIOLATED — $F check(s) failing"
fi
[ "$F" -eq 0 ]
