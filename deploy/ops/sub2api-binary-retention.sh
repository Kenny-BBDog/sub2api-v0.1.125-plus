#!/usr/bin/env bash
set -euo pipefail

DIR=${DIR:-/root/sub2api-gray}
KEEP=${KEEP:-6}

cd "$DIR"
mapfile -t candidates < <(
  find . -maxdepth 1 -type f \
    \( -name 'server.*' -o -name 'sub2api*linux*' \) \
    ! -name 'server.embedhotfix.linux' \
    ! -name 'server.v0.1.125-plus.wshotfix.new' \
    -printf '%T@ %p\n' | sort -nr | awk '{print $2}'
)

count=${#candidates[@]}
if (( count <= KEEP )); then
  echo "$(date -u +%FT%TZ) ok count=$count keep=$KEEP deleted=0"
  exit 0
fi

deleted=0
for ((i=KEEP; i<count; i++)); do
  target=${candidates[$i]}
  case "$target" in
    ./*)
      rm -f -- "$target"
      deleted=$((deleted + 1))
      ;;
  esac
done

echo "$(date -u +%FT%TZ) ok count=$count keep=$KEEP deleted=$deleted"
