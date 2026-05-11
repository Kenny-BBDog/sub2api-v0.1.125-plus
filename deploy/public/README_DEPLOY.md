# Sub2API v0.1.125-plus Clean Deployment Package

This package contains a clean deployable build of Sub2API v0.1.125-plus.

It intentionally does not contain:

- Production database data.
- Account pool data, access tokens, refresh tokens, or OAuth session data.
- Production `.env`, systemd units, Docker volumes, logs, backups, or host-specific nginx config.
- Any upstream API keys.

## Files

- `bin/sub2api-linux-amd64`: embedded Linux amd64 server binary.
- `docker-compose.yml`: fresh PostgreSQL + Redis + Sub2API deployment.
- `.env.example`: sanitized configuration template.
- `generate-env.sh` / `generate-env.ps1`: local secret generator for `.env`.
- `SHA256SUMS`: binary checksum.

## Quick Start

Linux:

```sh
chmod +x bin/sub2api-linux-amd64 generate-env.sh
./generate-env.sh
docker compose up -d
docker compose logs -f sub2api
```

Windows PowerShell:

```powershell
.\generate-env.ps1
docker compose up -d
docker compose logs -f sub2api
```

Open:

```text
http://127.0.0.1:18084/admin/dashboard
```

The initial admin account is controlled by `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`.

## Notes For Recipients

This starts with an empty database. Add your own upstream accounts, API keys, models, pricing, and routing settings from the admin dashboard.

If you need a public HTTPS domain, put nginx/Caddy/Cloudflare in front of `127.0.0.1:18084`. Do not copy a production systemd unit or nginx file from another deployment because those files usually contain host-specific secrets or domains.

For OpenAI-compatible Codex CLI usage, point Codex to:

```toml
model_provider = "openai"
model = "gpt-5.4"
openai_base_url = "https://YOUR_DOMAIN/v1"
openai_api_key = "YOUR_SUB2API_KEY"
```

