# sub2api v0.1.125-plus

Personal modified public fork of Sub2API v0.1.125, focused on OpenAI-compatible routing and Codex CLI stability.

This repository contains source code only. It does not include production databases, account pools, OAuth refresh tokens, API keys, proxy credentials, server passwords, `.env` files, generated binaries, or upload chunks.

[中文说明](README_CN.md) | English | [日本語](README_JA.md)

## What Is Different

- Codex CLI compatibility for the built-in `model_provider = "openai"` configuration, which preserves local session history.
- More robust OpenAI Responses and WebSocket forwarding behavior.
- WebSocket ctx pool queueing and lifecycle fixes for Codex CLI 0.130+ built-in OpenAI traffic.
- Safer OpenAI OAuth refresh behavior for bad or already-reused refresh tokens.
- Reduced noisy refresh retries by archiving bad accounts instead of repeatedly scheduling them.
- Admin usage and request accounting fixes used by the modified deployment.
- Embedded Google OAuth client IDs/secrets were removed from public source and must be provided at runtime.

## Recommended Codex CLI Config

Use the built-in `openai` provider when preserving existing Codex local sessions is the priority. Codex CLI 0.130+ uses WebSocket for this path.

```toml
model_provider = "openai"
model = "gpt-5.4"
model_reasoning_effort = "medium"
network_access = "enabled"
windows_wsl_setup_acknowledged = true
model_context_window = 500000

openai_base_url = "https://your-domain.example/v1"
openai_api_key = "sk-your-api-key"
```

`responses_websockets_v2` is a removed feature flag in Codex CLI 0.130+ and did not affect transport selection in testing:

```toml
[features]
responses_websockets_v2 = true
```

Use a custom provider for HTTP/SSE. Codex treats this as a different provider, so existing sessions require local migration or copying before they appear:

```toml
model_provider = "OpenAI"
model = "gpt-5.4"
review_model = "gpt-5.4"
model_reasoning_effort = "medium"
network_access = "enabled"
windows_wsl_setup_acknowledged = true
model_context_window = 500000

openai_api_key = "sk-your-api-key"

[model_providers.OpenAI]
name = "OpenAI"
base_url = "https://your-domain.example"
wire_api = "responses"
requires_openai_auth = true
```

Validate your own deployment with long streaming requests and concurrent Codex CLI terminals before relying on it in production.

## Build From Source

```bash
git clone https://github.com/Kenny-BBDog/sub2api-v0.1.125-plus.git
cd sub2api-v0.1.125-plus
```

Build frontend:

```bash
cd frontend
pnpm install
pnpm build
```

Build backend with embedded frontend assets:

```bash
cd ../backend
go mod download
go build -tags embed -o sub2api ./cmd/server
```

Runtime requirements depend on your configuration, but typically include PostgreSQL 15+, Redis 7+, a backend config or environment file, admin credentials, upstream account credentials, and optional proxy settings.

## Reverse Proxy Notes

For Nginx in front of Codex CLI / Responses / WebSocket traffic, verify long timeouts and upgrade headers:

```nginx
underscores_in_headers on;

proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

## OAuth Secrets

This public fork does not embed third-party OAuth secrets. Configure them at runtime if you need those integrations:

```bash
GEMINI_CLI_OAUTH_CLIENT_ID=your-client-id
GEMINI_CLI_OAUTH_CLIENT_SECRET=your-client-secret
ANTIGRAVITY_OAUTH_CLIENT_ID=your-client-id
ANTIGRAVITY_OAUTH_CLIENT_SECRET=your-client-secret
```

## Security

Before publishing, this repository was scanned with Gitleaks:

```bash
gitleaks git --redact --verbose .
gitleaks dir --redact --verbose .
```

Both scans passed with `no leaks found`. The repository-specific `.gitleaks.toml` keeps default rules enabled and only allowlists known test fixtures, documentation placeholders, and confirmed SQL-field false positives.

## Upstream

This is not an official Sub2API release. It is a personal modified fork for Codex CLI / OpenAI provider / Responses / WebSocket / account-pool stability work.

## License

See [LICENSE](LICENSE).
