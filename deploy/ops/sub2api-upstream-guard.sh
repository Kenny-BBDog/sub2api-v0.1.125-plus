#!/bin/sh
set -eu

SITE_CONF=${SITE_CONF:-/etc/nginx/sites-enabled/sub2api.conf}
APP_PORT=${APP_PORT:-18084}
LOG_FILE=${LOG_FILE:-/var/log/sub2api-upstream-guard.log}

timestamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log_line() { printf '%s %s\n' "$(timestamp)" "$1" >> "$LOG_FILE"; }

current_port=$(python3 - "$SITE_CONF" <<'PY'
from pathlib import Path
import re
import sys

text = Path(sys.argv[1]).read_text()
m = re.search(r'upstream\s+sub2api_backend\s*\{[^}]*server\s+127\.0\.0\.1:(\d+);', text, re.S)
print(m.group(1) if m else '')
PY
)

check_target() {
  port=$1
  curl -k -sS --connect-timeout 3 --max-time 8 -o /dev/null -w '%{http_code}' "http://127.0.0.1:${port}/healthz" 2>/dev/null | grep -qx '200'
}

if [ "$current_port" != "$APP_PORT" ]; then
  log_line "wrong-upstream current_port=$current_port target_port=$APP_PORT correcting=true"
  TARGET_PORT=$APP_PORT /root/sub2api-gray/switch_nginx_to_live.sh >/dev/null
  exit 0
fi

if ! check_target "$APP_PORT"; then
  log_line "app-unhealthy current_port=$current_port action=restart-sub2api"
  systemctl restart sub2api-embedhotfix.service || true
  exit 0
fi

exit 0
