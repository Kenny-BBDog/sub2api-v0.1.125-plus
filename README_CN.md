# sub2api v0.1.125-plus

这是基于 Sub2API v0.1.125 的个人魔改公开版，主要目标是让 OpenAI / Codex CLI 场景更稳定，尤其是 `model_provider = "openai"` + `openai_base_url = ".../v1"` 这类客户端配置。

本仓库只发布源码和可复现的工程文件，不包含任何生产数据库、账号池、OAuth refresh token、API Key、代理密码、服务器密码、`.env`、构建二进制或上传分片。

## 这个版本改了什么

- **Codex CLI OpenAI provider 兼容**：面向 Codex CLI 的 `openai` provider 配置做了兼容，避免必须伪装成自定义 `OpenAI` provider 才能走 Responses API。
- **Responses / WebSocket 路由增强**：补强 OpenAI Responses、WebSocket 转发、完成事件、断联处理和长流式请求稳定性。
- **WS 并发槽优化**：为 WebSocket ctx pool 增加等待队列和更稳的连接生命周期处理，降低多终端、多 subagent 并发时的偶发断流。
- **OpenAI OAuth 账号刷新保护**：对已知坏账号/刷新失败账号做归档和暂停刷新，减少 `refresh_token_reused` 这类噪音反复刷屏，避免多个刷新路径竞态销号。
- **账号池运行方式更稳**：默认面向 WS + ctx pool 的账号池使用方式，降低 Codex CLI 长任务过程中账号切换、流断开和连接关闭问题。
- **管理后台和使用记录修补**：修复部分使用记录、请求类型、流式统计、后台展示和时区相关问题。
- **公开仓库安全处理**：移除了内置 Google OAuth Client ID/Secret，改为运行时通过环境变量或后台配置注入。

## 推荐的 Codex CLI 配置

这个 fork 重点验证的是 Codex CLI 使用标准 `openai` provider 写法：

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

正常情况下不需要额外开启：

```toml
[features]
responses_websockets_v2 = true
```

如果你自己改了 Codex CLI 版本、代理链、Nginx 或账号池策略，仍然建议先做长流式请求和多终端并发测试。

## 部署说明

当前仓库没有发布预编译 Release。建议从源码构建：

```bash
git clone https://github.com/Kenny-BBDog/sub2api-v0.1.125-plus.git
cd sub2api-v0.1.125-plus
```

前端构建：

```bash
cd frontend
pnpm install
pnpm build
```

后端构建：

```bash
cd ../backend
go mod download
go build -tags embed -o sub2api ./cmd/server
```

运行前需要准备：

- PostgreSQL 15+
- Redis 7+，如果你的配置启用了 Redis
- 后端配置文件或环境变量
- 管理员账号和 JWT/TOTP 等密钥
- 上游账号、OAuth 凭据、代理配置

不要把生产 `.env`、数据库备份、账号导出、refresh token、API key 或代理密码提交到仓库。

## Nginx 注意事项

如果前面有 Nginx，建议至少确认：

```nginx
underscores_in_headers on;

proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

长流式和 WebSocket 场景对超时、升级头、反代缓冲很敏感。生产部署前请用 Codex CLI 做长任务压测。

## OAuth 凭据

公开仓库不会内置第三方 OAuth client secret。需要相关功能时，请通过环境变量或后台配置注入：

```bash
GEMINI_CLI_OAUTH_CLIENT_ID=your-client-id
GEMINI_CLI_OAUTH_CLIENT_SECRET=your-client-secret
ANTIGRAVITY_OAUTH_CLIENT_ID=your-client-id
ANTIGRAVITY_OAUTH_CLIENT_SECRET=your-client-secret
```

## 安全验证

本仓库已加入 `.gitleaks.toml`，保留默认规则，只对测试 fixture、文档示例和已确认误报做窄豁免。

发布前已验证：

```bash
gitleaks git --redact --verbose .
gitleaks dir --redact --verbose .
```

结果均为 `no leaks found`。

## 和上游的关系

这是个人魔改 fork，不是 Sub2API 官方发行版。上游项目的完整功能、文档和许可证请以原项目为准。本 fork 的重点是 Codex CLI / OpenAI provider / Responses / WebSocket / 账号池稳定性。

## License

沿用原项目许可证，见 [LICENSE](LICENSE)。
