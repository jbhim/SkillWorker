---
name: bailian-coding-plan
description: Use when needing to switch Claude Code model to Alibaba Bailian platform models by modifying configuration file
---

# 百炼编程计划

## 概述

在 Claude Code 中切换至阿里云百炼平台的大语言模型。通过修改 `~/.claude/settings.json` 中的 `env.ANTHROPIC_MODEL` 配置实现模型切换，重启后生效。

## 何时使用

- 需要切换 Claude Code 使用的模型至百炼平台
- 需要特定模型能力（文本生成、深度思考、视觉理解）
- 需要修改 `~/.claude/settings.json` 中的 `ANTHROPIC_MODEL` 环境变量

**支持的品牌与模型：**

| 品牌 | 模型 | 能力 |
|------|------|------|
| 千问 | qwen3.5-plus | 文本生成、深度思考、视觉理解 |
| 千问 | qwen3-max-2026-01-23 | 文本生成、深度思考 |
| 千问 | qwen3-coder-next | 文本生成 |
| 千问 | qwen3-coder-plus | 文本生成 |
| 智谱 | glm-5 | 文本生成、深度思考 |
| 智谱 | glm-4.7 | 文本生成、深度思考 |
| Kimi | kimi-k2.5 | 文本生成、深度思考、视觉理解 |
| MiniMax | MiniMax-M2.5 | 文本生成、深度思考 |

## 快速参考

**使用方法：**

```bash
/skill bailian-coding-plan
```

**工作流程：**
1. 展示按品牌分组的可用模型列表
2. 提示用户选择目标模型
3. 读取并修改 `~/.claude/settings.json` 中的 `env.ANTHROPIC_MODEL`
4. 保留其他 env 配置不变
5. 提示用户重启 Claude Code 使配置生效

## 实现

**模型选择流程：**

```
用户调用技能
    ↓
展示按品牌和能力分组的模型列表
    ↓
提示用户输入选择（1-8）
    ↓
读取 ~/.claude/settings.json
    ↓
修改 env.ANTHROPIC_MODEL 值
    ↓
保留其他 env 配置不变
    ↓
写回配置文件
    ↓
提示重启 Claude Code 使配置生效
```

**切换方式：**

修改 Claude Code 用户级配置文件：

| 平台 | 配置文件路径 |
|------|-------------|
| Windows | `%USERPROFILE%\.claude\settings.json` |
| macOS/Linux | `~/.claude/settings.json` |

**配置文件修改：**

```json
{
  "env": {
    "ANTHROPIC_MODEL": "<model-name>"
  }
}
```

如果 `env` 字段已存在其他配置（如 `ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL`），只需修改 `ANTHROPIC_MODEL` 的值，保留其他配置不变。

修改后重启 Claude Code 生效。

**模型配置映射：**

| 模型名称 | 配置值 |
|----------|--------|
| qwen3.5-plus | `qwen3.5-plus` |
| qwen3-max-2026-01-23 | `qwen3-max-2026-01-23` |
| qwen3-coder-next | `qwen3-coder-next` |
| qwen3-coder-plus | `qwen3-coder-plus` |
| glm-5 | `glm-5` |
| glm-4.7 | `glm-4.7` |
| kimi-k2.5 | `kimi-k2.5` |
| MiniMax-M2.5 | `MiniMax-M2.5` |

## 常见错误

- **选择不适合任务的模型**：查看能力列——视觉理解任务需要选择支持视觉的模型
- **未重启 Claude Code**：修改配置文件后必须重启才能生效
- **误删其他 env 配置**：修改时保留 `ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL` 等其他环境变量
- **配置文件路径错误**：Claude Code 配置文件在用户主目录下的 `.claude/settings.json`

## 使用示例

```
用户: /skill bailian-coding-plan

Claude: 可用的百炼平台模型：

【千问】
1. qwen3.5-plus - 文本生成、深度思考、视觉理解
2. qwen3-max-2026-01-23 - 文本生成、深度思考
3. qwen3-coder-next - 文本生成
4. qwen3-coder-plus - 文本生成

【智谱】
5. glm-5 - 文本生成、深度思考
6. glm-4.7 - 文本生成、深度思考

【Kimi】
7. kimi-k2.5 - 文本生成、深度思考、视觉理解

【MiniMax】
8. MiniMax-M2.5 - 文本生成、深度思考

请选择模型（输入数字 1-8）：

用户: 1

Claude: 正在切换至 qwen3.5-plus...

已修改配置文件：~\.claude\settings.json

```json
{
  "env": {
    "ANTHROPIC_MODEL": "qwen3.5-plus"
  }
}
```

其他 env 配置（如 ANTHROPIC_AUTH_TOKEN、ANTHROPIC_BASE_URL）保持不变。
请重启 Claude Code 使配置生效。
```
