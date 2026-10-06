#!/usr/bin/env bash
# Baut die Website und spielt sie in die interne Vorschau auf dem NAS ein:
#   http://192.168.178.40:8092/  (Container pgh-vorschau, nur Heimnetz, noindex)
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py --check
D=/share/CACHEDEV1_DATA/Container/pgh-vorschau/html
( cd dist && tar cf - . ) | ssh nas "rm -rf $D/* && tar xf - -C $D"
echo "Vorschau aktualisiert: http://192.168.178.40:8092/"
