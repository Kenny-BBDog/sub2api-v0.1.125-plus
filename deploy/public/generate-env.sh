#!/bin/sh
set -eu

if [ -f .env ]; then
  echo ".env already exists. Remove it first if you want to regenerate secrets." >&2
  exit 1
fi

secret() {
  bytes=$1
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex "$bytes"
  else
    dd if=/dev/urandom bs="$bytes" count=1 2>/dev/null | od -An -tx1 | tr -d ' \n'
  fi
}

sed \
  -e "s/change-me-postgres-password/$(secret 24)/" \
  -e "s/change-me-redis-password/$(secret 24)/" \
  -e "s/change-me-admin-password/$(secret 16)/" \
  -e "s/change-me-64-hex-jwt-secret/$(secret 32)/" \
  -e "s/change-me-64-hex-totp-key/$(secret 32)/" \
  .env.example > .env

echo "Generated .env. Review ADMIN_EMAIL and SERVER_PORT before starting."

