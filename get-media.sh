#!/bin/bash
# Downloads your pictures and downloadable files from Squarespace into this folder.
# Run it once (it's safe to run again: it skips anything already downloaded).
cd "$(dirname "$0")" || exit 1
total=$(wc -l < media-list.tsv | tr -d ' ')
n=0; got=0; failed=0
: > media-failed.txt
while IFS=$'\t' read -r url path; do
  n=$((n+1))
  if [ -s "$path" ]; then continue; fi
  mkdir -p "$(dirname "$path")"
  printf '\r%s of %s  ' "$n" "$total"
  if curl -fsSL --retry 5 --retry-delay 10 --retry-all-errors -A "Mozilla/5.0" -o "$path.part" "$url"; then
    mv "$path.part" "$path"; got=$((got+1))
  else
    rm -f "$path.part"; failed=$((failed+1)); printf '%s\t%s\n' "$url" "$path" >> media-failed.txt
  fi
  sleep 0.4
done < media-list.tsv
echo
echo "Done. Downloaded $got new file(s); $failed could not be downloaded."
if [ "$failed" -gt 0 ]; then echo "The ones that failed are listed in media-failed.txt."; fi
