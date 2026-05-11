# sub2api v0.1.125-plus

Sub2API v0.1.125 をベースにした個人向け改造 fork です。主な目的は OpenAI 互換ルーティングと Codex CLI の安定性改善です。

このリポジトリにはソースコードのみを含めています。本番データベース、アカウントプール、OAuth refresh token、API key、プロキシ認証情報、サーバーパスワード、`.env`、生成済みバイナリ、アップロード分割ファイルは含めていません。

[English](README.md) | [中文说明](README_CN.md) | 日本語

## 主な変更点

- Codex CLI の標準 `model_provider = "openai"` 設定への互換性改善。
- OpenAI Responses / WebSocket 転送の安定性改善。
- 長時間ストリーミングや複数 Codex CLI 端末向けの WebSocket ctx pool キュー処理。
- OpenAI OAuth refresh token の再利用・失敗アカウントに対する安全な扱い。
- 問題のあるアカウントを繰り返し自動更新せず、DB 内でアーカイブする運用。
- 管理画面の利用記録、リクエスト種別、時区関連の修正。
- Google OAuth Client ID/Secret は公開ソースから除去し、環境変数で注入する方式に変更。

## 推奨 Codex CLI 設定

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

通常は以下を有効にする必要はありません。

```toml
[features]
responses_websockets_v2 = true
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
