# sub2api v0.1.125-plus

Sub2API v0.1.125 をベースにした個人向け改造 fork です。主な目的は OpenAI 互換ルーティングと Codex CLI の安定性改善です。Codex CLI は HTTP/SSE を推奨し、既存の組み込み `openai` 履歴向けにローカル移行ツールを同梱しています。

このリポジトリにはソースコードのみを含めています。本番データベース、アカウントプール、OAuth refresh token、API key、プロキシ認証情報、サーバーパスワード、`.env`、生成済みバイナリ、アップロード分割ファイルは含めていません。

[English](README.md) | [中文说明](README_CN.md) | 日本語

## 主な変更点

- custom `OpenAI` provider と `wire_api = "responses"` を使う Codex CLI HTTP/SSE 推奨設定。
- OpenAI Responses / WebSocket 転送の安定性改善。
- Codex CLI 0.130+ の組み込み `openai` WebSocket 経路へのオプション互換性。
- OpenAI OAuth refresh token の再利用・失敗アカウントに対する安全な扱い。
- 問題のあるアカウントを繰り返し自動更新せず、DB 内でアーカイブする運用。
- 管理画面の利用記録、リクエスト種別、時区関連の修正。
- ローカル Codex 履歴移行ツール: `tools/codex-provider-migrate.py`。
- Google OAuth Client ID/Secret は公開ソースから除去し、環境変数で注入する方式に変更。

## 推奨 Codex CLI 設定

通常は HTTP/SSE を使用してください。

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

組み込み `openai` provider から custom `OpenAI` provider に切り替えたあと既存履歴が見えない場合は、Codex CLI を閉じてから以下を実行します。

```bash
python tools/codex-provider-migrate.py --apply --yes
```

このツールは対象 session ファイルと `state_*.sqlite` を先にバックアップします。`auth.json`、`config.toml`、API key、ログイン資格情報は変更しません。確認だけなら `--apply` を付けずに実行してください。

ローカル履歴をまだ移行したくない場合のみ、組み込み `openai` provider を使用できます。Codex CLI 0.130+ ではこの経路は WebSocket を使用します。

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

## ビルド

```bash
git clone https://github.com/Kenny-BBDog/sub2api-v0.1.125-plus.git
cd sub2api-v0.1.125-plus
cd frontend
pnpm install
pnpm build
cd ../backend
go mod download
go build -tags embed -o sub2api ./cmd/server
```

## セキュリティ

公開前に Gitleaks で検証済みです。

```bash
gitleaks git --redact --verbose .
gitleaks dir --redact --verbose .
```

結果はいずれも `no leaks found` です。

## 注意

これは Sub2API の公式リリースではありません。Codex CLI / OpenAI provider / Responses / WebSocket / アカウントプール安定性のための個人改造 fork です。

## License

[LICENSE](LICENSE) を参照してください。
