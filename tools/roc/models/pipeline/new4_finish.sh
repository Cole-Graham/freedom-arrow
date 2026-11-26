#!/usr/bin/env bash
# 26 Nov: finish Shawn's 4 new models (armory/battle .fam, cuts, glass, LOD1/LOD2, .fat). One at a time.
cd "$(dirname "$0")"
for a in "ah64e 16.4 60000 30000" "fck1 14.21 120000 55000" "c130 29.79 30000 30000" "chx2 6.6 15000 15000"; do
  set -- $a; echo "== $1 $(date +%T)"; ./finish_one.sh $1 $2 $3 $4 2>&1 | tail -8; done; echo ALLFIN
