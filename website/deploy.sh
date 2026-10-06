#!/usr/bin/env bash
# Lädt website/dist per SFTP auf das Hetzner-Webhosting (public_html).
# Zugangsdaten: ~/.config/pgh-brandschutz/hetzner.env mit FTP_HOST und FTP_USER,
# Authentifizierung per Schlüssel ~/.ssh/id_hetzner_webhosting_pgh (kein Passwort).
# ACHTUNG: Erst ausführen, wenn Patrick die Seite freigegeben hat (Stand 06.10.2026: noch NICHT online).
set -euo pipefail
cd "$(dirname "$0")"
source ~/.config/pgh-brandschutz/hetzner.env
python3 build.py --check
if python3 build.py --check | grep -q "^[1-9][0-9]* offene Stellen"; then
  echo "Abbruch: Es gibt noch [OFFEN: ...]-Stellen." >&2; exit 1
fi
batch=$(mktemp)
( cd dist
  echo "-rm public_html/index.htm"   # Hetzner-Platzhalterseite entfernen (würde sonst evtl. vor index.html greifen)
  find . -type d | sed 's|^\./||' | grep -v '^\.$' | sed 's|^|-mkdir public_html/|'
  find . -type f | sed 's|^\./||' | while read -r f; do echo "put \"$f\" \"public_html/$f\""; done ) > "$batch"
( cd dist && sftp -b "$batch" -i ~/.ssh/id_hetzner_webhosting_pgh -o IdentitiesOnly=yes "$FTP_USER@$FTP_HOST" )
rm -f "$batch"
echo "Hochgeladen. Prüfen: https://www.pgh-brandschutz.de/"
