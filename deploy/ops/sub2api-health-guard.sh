#!/bin/sh
set -eu

LOG=${LOG:-/var/log/sub2api/health-guard.log}
APP_PORT=${APP_PORT:-18084}
PUBLIC_HOSTNAME=${PUBLIC_HOSTNAME:-}

now() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "$(now) $*" >> "$LOG"; }

restart_sub2api() {
  log "restart sub2api-embedhotfix: $1"
  systemctl restart sub2api-embedhotfix.service || log "restart sub2api failed"
  sleep 5
}

restart_egress() {
  log "restart sub2api-egress-socks: $1"
  systemctl restart sub2api-egress-socks.service || log "restart egress failed"
  sleep 3
}

restart_nginx() {
  log "reload nginx: $1"
  nginx -t >/dev/null 2>&1 && systemctl reload nginx || systemctl restart nginx || log "nginx recover failed"
  sleep 2
}

code_of() {
  curl -k -sS --connect-timeout 3 --max-time 8 -o /dev/null -w '%{http_code}' "$@" 2>/dev/null || echo 000
}

if ! systemctl is-active --quiet sub2api-embedhotfix.service; then
  restart_sub2api "service inactive"
fi

if ! docker inspect -f '{{.State.Running}}' sub2api-embedhotfix 2>/dev/null | grep -qx true; then
  restart_sub2api "container not running"
fi

local_admin=$(code_of "http://127.0.0.1:${APP_PORT}/admin/dashboard")
if [ "$local_admin" != 200 ]; then
  restart_sub2api "local admin returned $local_admin"
fi

local_health=$(code_of "http://127.0.0.1:${APP_PORT}/healthz")
if [ "$local_health" != 200 ]; then
  restart_sub2api "local healthz returned $local_health"
fi

if ! systemctl is-active --quiet sub2api-egress-socks.service; then
  restart_egress "service inactive"
fi

if command -v ss >/dev/null 2>&1 && ! ss -ltn | awk '{print $4}' | grep -q '172\.18\.0\.1:1080$'; then
  restart_egress "socks listener missing"
fi

if ! systemctl is-active --quiet nginx; then
  restart_nginx "nginx inactive"
fi

edge_admin=skipped
edge_health=skipped
if [ -n "$PUBLIC_HOSTNAME" ]; then
  edge_admin=$(code_of --resolve "${PUBLIC_HOSTNAME}:443:127.0.0.1" "https://${PUBLIC_HOSTNAME}/admin/dashboard")
  if [ "$edge_admin" != 200 ]; then
    restart_nginx "edge admin returned $edge_admin"
    edge_admin_after=$(code_of --resolve "${PUBLIC_HOSTNAME}:443:127.0.0.1" "https://${PUBLIC_HOSTNAME}/admin/dashboard")
    if [ "$edge_admin_after" != 200 ]; then
      restart_sub2api "edge admin still $edge_admin_after after nginx recover"
    fi
  fi
  edge_health=$(code_of --resolve "${PUBLIC_HOSTNAME}:443:127.0.0.1" "https://${PUBLIC_HOSTNAME}/healthz")
  if [ "$edge_health" != 200 ]; then
    restart_nginx "edge healthz returned $edge_health"
  fi
fi

log "ok local_admin=$local_admin local_health=$local_health edge_admin=$edge_admin edge_health=$edge_health"
