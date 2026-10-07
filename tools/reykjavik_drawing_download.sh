#!/bin/sh
# usage: fwget.sh <rendition href> <out.pdf>  (FotoWeb: request rendition, then poll until ready)
J=$(mktemp)
curl -sS -c "$J" -b "$J" --max-time 60 -X POST -H 'Content-Type: application/vnd.fotoware.rendition-request+json' \
  -H 'Accept: application/vnd.fotoware.rendition-response+json' -d "{\"href\":\"$1\"}" \
  https://skjalasafn.reykjavik.is/fotoweb/services/renditions | python3 -c 'import json,sys;print(json.load(sys.stdin)["href"])' > "$J.href"
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  code=$(curl -sS -c "$J" -b "$J" --max-time 120 -o "$2" -w '%{http_code}' "https://skjalasafn.reykjavik.is$(cat $J.href)")
  [ "$code" = 200 ] && break; sleep 3
done
echo "$code $(file -b "$2" | cut -c1-40)"
