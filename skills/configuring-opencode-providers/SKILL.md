---
name: configuring-opencode-providers
description: Use when configuring custom AI providers in OpenCode via opencode.json, especially OpenAI-compatible APIs, local models, or providers not in the /connect list
---

# 配置 OpenCode 自定义供应商

## 概述

在 OpenCode 中配置任何 OpenAI 兼容或自定义 API 供应商。支持本地模型（Ollama、LM Studio）、云 API 和自定义端点。

**关键区别**：不同 API 端点需要不同的 npm 包。选错会破坏工具调用。

## 何时使用

- 添加 `/connect` 列表中不存在的供应商
- 配置本地模型（Ollama、LM Studio、llama.cpp）
- 使用自定义 base URL 或 API 网关（Helicone、Cloudflare AI Gateway）
- 设置 VPC 端点或代理服务
- 配置具有不同 Token 限制的多模型

**何时不使用**：内置供应商如 Anthropic、OpenAI、Amazon Bedrock - 使用 `/connect` 命令即可。

## 快速参考

| 任务 | 配置位置 |
|------|----------|
| 设置 API 端点 | `provider.{id}.options.baseURL` |
| 使用环境变量存储密钥 | `options.apiKey: "{env:VAR_NAME}"` |
| 添加自定义请求头 | `options.headers: { "Header": "value" }` |
| 设置模型 Token 限制 | `models.{id}.limit: { context: N, output: N }` |
| Chat/completions API | `npm: "@ai-sdk/openai-compatible"` |
| Responses API | `npm: "@ai-sdk/openai"` |

## 配置文件位置

`opencode.json` 可以放在以下位置（优先级从低到高）：

| 位置 | 路径 | 适用场景 |
|------|------|----------|
| 全局配置 | `~/.config/opencode/opencode.json` | 用户级偏好、常用供应商 |
| 项目配置 | `项目根目录/opencode.json` | 项目特定设置、团队协作 |
| 自定义路径 | `OPENCODE_CONFIG` 环境变量指向的文件 | 临时覆盖 |

**建议：**
- 本地模型配置放在**全局配置**（对所有项目可用）
- 项目特定的供应商放在**项目配置**（提交到 Git，团队成员共享）

## 实现步骤

### 步骤 1：在 opencode.json 中配置供应商

**关键：根据 API 端点选择正确的 npm 包**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "myprovider": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "我的自定义供应商",
      "options": {
        "baseURL": "https://api.myprovider.com/v1",
        "apiKey": "{env:MYPROVIDER_API_KEY}"
      },
      "models": {
        "model-id": {
          "name": "模型显示名称",
          "limit": {
            "context": 128000,
            "output": 4096
          }
        }
      }
    }
  }
}
```

**说明：**
- `myprovider` 是自定义的供应商 ID，可以是任意字符串（如 `ollama`、`custom-api`）
- 本地模型（Ollama、LM Studio）不需要 API key，可以跳过步骤 2

### 步骤 2：存储 API 凭证（如需要）

如果供应商需要 API key，使用 `/connect` 存储：

```bash
# 运行 /connect
/connect

# 选择底部的 "Other"
# 输入步骤 1 中定义的供应商 ID（如 "myprovider"）
# 输入 API 密钥
```

**凭据存储位置：** 使用 `/connect` 添加的 API 密钥会存储在 `~/.local/share/opencode/auth.json` 中

**注意：** 本地模型（Ollama、llama.cpp、LM Studio）通常不需要此步骤

### NPM 包选择（关键）

**使用 `@ai-sdk/openai-compatible`** 适用于：
- `/v1/chat/completions` 端点
- 大多数 OpenAI 兼容供应商（OpenRouter、Together AI 等）
- 本地服务器（Ollama、LM Studio，端口 1234）

**使用 `@ai-sdk/openai`** 适用于：（：
- `/v1/responses` 端点
- OpenAI 的 responses API

```json5
// OpenAI 兼容（chat/completions
"npm": "@ai-sdk/openai-compatible"

// OpenAI responses API
"npm": "@ai-sdk/openai"
```

### 配置字段说明

**Provider 级别（`provider.{id}`）：**

| 字段 | 必需 | 说明 |
|------|------|------|
| `npm` | 是 | AI SDK 包名 |
| `name` | 是 | UI 中显示的名称 |
| `options.baseURL` | 是 | API 端点 URL |
| `options.apiKey` | 通常 | 使用 `{env:VAR}` 语法 |
| `options.headers` | 否 | 自定义 HTTP 请求头 |
| `models` | 是 | 模型配置映射 |


**Model 级别（`models.{model-id}`）：**

| 字段 | 说明 |
|------|--------|
| `name` | 模型选择器中显示的名称 |
| `limit.context` | 最大输入 Token（模型容量） |
| `limit.output` | 最大输出 Token |

### 配置示例

**本地 Ollama：**
```json
{
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (本地)",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      },
      "models": {
        "llama2": { "name": "Llama 2" }
      }
    }
  }
}
```

**带自定义请求头（如 Helicone）：**
```json
{
  "provider": {
    "helicone": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Helicone",
      "options": {
        "baseURL": "https://ai-gateway.helicone.ai",
        "headers": {
          "Helicone-Cache-Enabled": "true",
          "Helicone-User-Id": "user-123"
        }
      }
    }
  }
}
```

**多模型与限制：**
```json
{
  "provider": {
    "custom": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "自定义 API",
      "options": {
        "baseURL": "https://api.example.com/v1",
        "apiKey": "{env:CUSTOM_API_KEY}"
      },
      "models": {
        "small": {
          "name": "小模型",
          "limit": { "context": 32000, "output": 4096 }
        },
        "large": {
          "name": "大模型",
          "limit": { "context": 128000, "output": 8192 }
        }
      }
    }
  }
}
```

## 常见错误

| 错误 | 修正 |
|------|------|
| chat/completions 使用 `@ai-sdk/openai` | 改用 `@ai-sdk/openai-compatible` |
| `limit` 放在 provider 级别 | 移到 `models.{id}.limit` |
| 写 `$API_KEY` 或明文 | 使用 `"{env:API_KEY}"` 语法 |
| 忘记 `npm` 字段 | 必需 - 决定使用哪个 SDK |
| 混淆 `context` 和 `output` | `context` = 输入容量，`output` = 生成限制 |

## 验证

```bash
# 检查供应商是否出现
/models

# 测试供应商
opencode run "Hello from my custom provider"
```

## 环境变量

**格式：** `"{env:VARIABLE_NAME}"`

**示例：**
```json
"apiKey": "{env:CUSTOM_API_KEY}"
```

如果环境变量未设置，它会成为空字符串。

## 文件引用

**格式：** `"{file:path/to/file}"`

**示例：**
```json
"apiKey": "{file:~/.secrets/api-key}"
```
