# CiteWeave for DeepSeek Harness

**为 Agent 回答提供网页证据与可溯源配图。**

[English](README.md) · [CiteWeave](../../README.zh-CN.md) · [API 文档](../../docs/API.md) · [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)

CiteWeave 为 DeepSeek Harness 注册 `citeweave_search` 工具，检索公开网页、描述图片内容并筛选相关插图。Harness 根据返回的证据生成回答，在正文中展示图片并引用原始来源。

- 自动联网搜索，或指定最多五个来源页面。
- 图片内容描述、相关性排序与来源关联。
- 图片持久化存储，复用 Harness 原生 Markdown 展示。
- CiteWeave 后端独立部署，无需修改 Harness。

## 运行要求

- DeepSeek Harness `0.2.1-rc.2`，Node.js 24 或以上。
- 基于 [`feature/deepseek-harness-images` 分支](https://github.com/wavachao/citeweave/tree/feature/deepseek-harness-images)部署的 CiteWeave 后端，且 Harness 主机能够访问该服务。
- 后端所需的 Linux、Python 与 NVIDIA GPU 环境，详见[部署指南](../../docs/DEPLOYMENT.md)。

## 安装

### 启动后端

```sh
git clone --branch feature/deepseek-harness-images https://github.com/wavachao/citeweave.git
cd citeweave
uv sync --frozen
cp .env.example .env
uv run python scripts/download_models.py
uv run python -m citeweave serve
```

后端默认监听 `http://127.0.0.1:8765`。通过网络部署时需配置访问令牌。容器、鉴权和模型安装见[部署指南](../../docs/DEPLOYMENT.md)；可选安装[已训练的图片排序模型](../../README.zh-CN.md#快速开始)。

### 安装插件

在另一个终端中，从仓库根目录执行：

```sh
cd plugins/deepseek-harness
npm ci
dsh plugin --profile web add "$PWD"
```

插件以 ES 模块直接加载，无需构建。在其他 Harness 主机安装时，可执行 `npm pack`，将生成的归档传输到目标主机后安装：

```sh
dsh plugin --profile web add /absolute/path/dsh-citeweave-0.1.0.tgz
```

### 连接 Harness

在启动 Harness 的环境中设置后端地址：

```sh
export CITEWEAVE_ENDPOINT=http://127.0.0.1:8765
dsh --profile web
```

后端启用鉴权时，同时将 `CITEWEAVE_ACCESS_TOKEN` 设置为后端的工作区令牌。PowerShell 使用 `$env:CITEWEAVE_ENDPOINT='http://127.0.0.1:8765'` 和 `$env:CITEWEAVE_ACCESS_TOKEN='<workspace-token>'`。

远程后端可通过 HTTPS 地址或 SSH 隧道连接。图片由 Harness 主机下载，浏览器无需直接访问 CiteWeave。

## 使用

在聊天中提出适合配图的问题：

> 解释埃拉托色尼如何测量地球周长，配上相关示意图并注明出处。

Harness 可根据请求选择 `citeweave_search`。工具也支持指定来源 URL，以限定检索范围。

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `query` | string | 必填，问题或检索主题。 |
| `urls` | string[] | 可选，1–5 个公开来源页面；省略时自动搜索。 |
| `verify_images` | boolean | 生成候选图片的视觉内容描述，默认 `true`。 |
| `refresh` | boolean | 绕过近期证据缓存，默认 `false`。 |

最终回答由 Harness 生成。CiteWeave 通过 [`POST /api/evidence`](../../docs/API.md#post-apievidence)提供文字证据、选中的图片、内容说明及来源 URL。

## 配置

可通过环境变量设置连接参数，也可创建 `citeweave.config.yml` 直接配置插件：

```yaml
- id: citeweave
  config:
    endpoint: http://127.0.0.1:8765
    timeoutMs: 180000
    maxImages: 3
```

```sh
dsh --profile web --patch /absolute/path/citeweave.config.yml
```

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `endpoint` | `CITEWEAVE_ENDPOINT` 或 `http://127.0.0.1:8765` | CiteWeave 服务地址。 |
| `accessToken` | `CITEWEAVE_ACCESS_TOKEN` 或空 | 后端工作区令牌。 |
| `timeoutMs` | `180000` | 请求超时，单位为毫秒。 |
| `maxImages` | `3` | 每次检索的最大图片数，范围为 1–8。 |

非空的 `endpoint` 和 `accessToken` 配置优先于环境变量。

## 运行说明

选中的图片导入 Harness 持久附件存储，工具返回原生 Markdown 渲染器可读取的本地图片路径，图片链接不包含后端凭据。Harness 文件系统提供方需能访问附件路径；远程执行环境需要配置对应的路径映射。

图片数量取决于来源可用性和内容相关性。没有合适图片时返回文字证据；单张图片下载失败时，其余证据仍可使用，并附带检索说明。后端忙碌时返回 `409`，当前请求完成后可重试。

## 开发

```sh
npm ci
npm test
npm pack --dry-run
```

## 许可

[MIT](LICENSE)。检索到的图片和来源内容遵循各自许可。
