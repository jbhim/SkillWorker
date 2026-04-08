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

**支持的品牌：**

| 品牌 | 可用模型 |
|------|----------|
| 千问 | qwen3.5-plus, qwen3-max-2026-01-23, qwen3-coder-next, qwen3-coder-plus |
| 智谱 | glm-5, glm-4.7 |
| Kimi | kimi-k2.5 |
| MiniMax | MiniMax-M2.5 |

**模型能力对照：**

| 模型 | 能力 |
|------|------|
| qwen3.5-plus | 文本生成、深度思考、视觉理解 |
| qwen3-max-2026-01-23 | 文本生成、深度思考 |
| qwen3-coder-next | 文本生成 |
| qwen3-coder-plus | 文本生成 |
| glm-5 | 文本生成、深度思考 |
| glm-4.7 | 文本生成、深度思考 |
| kimi-k2.5 | 文本生成、深度思考、视觉理解 |
| MiniMax-M2.5 | 文本生成、深度思考 |

## 快速参考

**使用方法：**

```bash
/skill bailian-coding-plan
```

**工作流程：**
1. 由于模型选项超过 4 个，使用以下两种方式之一让用户选择模型：
   - **方式一（分步选择）**：先用 `AskUserQuestion` 展示品牌选项（单选）：千问、智谱、Kimi、MiniMax，然后展示该品牌下的具体模型
   - **方式二（直接输入）**：让用户直接输入想要的模型名称（如 `kimi-k2.5`）
2. 获取目标模型名称
3. 读取并修改 `~/.claude/settings.json` 中的 `env.ANTHROPIC_MODEL`
4. 保留其他 env 配置不变
5. 提示用户选择切换方式：
   - 使用 `/model <model-name>` 立即切换当前会话（注意：不带双引号）
   - 或重启 Claude Code 使配置永久生效

## 实现

**模型选择流程：**

```
用户调用技能
    ↓
展示可用模型列表（8个模型）
    ↓
选择交互方式（二选一）：
├─ 方式一：分步选择
│   ├─ 使用 AskUserQuestion 展示品牌选项（4个品牌）
│   ├─ 用户选择品牌
│   └─ 使用 AskUserQuestion 展示该品牌下的模型
└─ 方式二：直接输入
    └─ 提示用户直接输入模型名称
    ↓
用户选择/输入目标模型
    ↓
读取 ~/.claude/settings.json
    ↓
修改 env.ANTHROPIC_MODEL 值
    ↓
保留其他 env 配置不变
    ↓
写回配置文件
    ↓
提示用户：可重启 Claude Code 或使用 /model 命令立即切换
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
- **未重启 Claude Code**：修改配置文件后必须重启才能永久生效（或使用 `/model` 命令立即切换当前会话）
- **误删其他 env 配置**：修改时保留 `ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL` 等其他环境变量
- **配置文件路径错误**：Claude Code 配置文件在用户主目录下的 `.claude/settings.json`

## 使用示例

### 方式一：分步选择

```
用户: /skill bailian-coding-plan

Claude: 正在获取可用的百炼平台模型...

**第一步：选择品牌**
[使用 AskUserQuestion 工具展示品牌选项]

请选择模型品牌：
○ 千问 (Qwen系列)
○ 智谱 (GLM系列)
○ Kimi
○ MiniMax

[用户选择: Kimi]

**第二步：选择具体模型**
[使用 AskUserQuestion 工具展示 Kimi 品牌下的模型]

请选择 Kimi 模型：
○ kimi-k2.5 - 文本生成、深度思考、视觉理解

[用户选择: kimi-k2.5]

Claude: 正在切换至 kimi-k2.5...
```

### 方式二：直接输入模型名称

```
用户: /skill bailian-coding-plan

Claude: 正在获取可用的百炼平台模型...

可用模型列表：
- 千问: qwen3.5-plus, qwen3-max-2026-01-23, qwen3-coder-next, qwen3-coder-plus
- 智谱: glm-5, glm-4.7
- Kimi: kimi-k2.5
- MiniMax: MiniMax-M2.5

请直接输入您要使用的模型名称：kimi-k2.5

Claude: 正在切换至 kimi-k2.5...
```

### 配置完成后的提示

```
已修改配置文件：~\.claude\settings.json

```json
{
  "env": {
    "ANTHROPIC_MODEL": "kimi-k2.5"
  }
}
```

其他 env 配置（如 ANTHROPIC_AUTH_TOKEN、ANTHROPIC_BASE_URL）保持不变。

**切换方式（二选一）：**
1. **立即生效（推荐）**：使用命令 `/model kimi-k2.5` 将当前会话切换到新模型（注意：不带双引号）
2. **下次生效**：重启 Claude Code 使配置永久生效
```
