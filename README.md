# SkillWorker

个人 Claude Code Skills 开发仓库，用于管理和开发自定义技能。

## 项目结构

```
.
├── CLAUDE.md                       # 项目开发规范
├── README.md                       # 本文件
└── skills/                         # Skill 目录
    ├── bailian-coding-plan/        # 百炼模型切换 Skill
    ├── configuring-opencode-providers/  # OpenCode 供应商配置指南
    └── mdf-script-development/     # 用友 MDF 前端脚本开发 Skill
        ├── SKILL.md                # 主入口
        ├── api-reference.md        # API 参考
        ├── lifecycle-events.md     # 生命周期事件
        ├── common-patterns.md      # 常见开发模式
        ├── business-patterns.md    # 业务场景模式
        └── examples.md             # 完整脚本示例
```

## 使用方法

### 安装 Skills 到 Claude Code

```bash
# 安装整个仓库
npx skills add ./skills

# 或从远程仓库安装
npx skills add jbhim/SkillWorker

# 安装单个 skill
npx skills add ./skills/mdf-script-development
```

### 使用 Skill

```bash
/skill bailian-coding-plan
/skill mdf-script-development
```

### 其他命令

```bash
# 查看已安装的 skills
npx skills list

# 移除 skill
npx skills remove <skill-name>

# 重新加载 plugins
npx skills reload
```

## Skill 列表

### bailian-coding-plan

切换 Claude Code 模型至阿里云百炼平台的大语言模型。

**支持的模型：**

| 品牌      | 模型                   | 能力             |
|---------|----------------------|----------------|
| 千问      | qwen3.5-plus         | 文本生成、深度思考、视觉理解 |
| 千问      | qwen3-max-2026-01-23 | 文本生成、深度思考      |
| 千问      | qwen3-coder-next     | 文本生成           |
| 千问      | qwen3-coder-plus     | 文本生成           |
| 智谱      | glm-5                | 文本生成、深度思考      |
| 智谱      | glm-4.7              | 文本生成、深度思考      |
| Kimi    | kimi-k2.5            | 文本生成、深度思考、视觉理解 |
| MiniMax | MiniMax-M2.5         | 文本生成、深度思考      |

**配置方式：**

修改 `~/.claude/settings.json` 中的 `env.ANTHROPIC_MODEL` 字段，重启后生效。

### configuring-opencode-providers

OpenCode 自定义 AI 供应商配置指南，适用于 OpenAI 兼容 API、本地模型等不在 `/connect` 列表中的提供商。

### mdf-script-development

用友 MDF（模型驱动框架）前端脚本开发技能，覆盖单据页/列表页的全场景开发指南。

**覆盖内容：**

- 完整 API 参考（viewModel、cb.rest、cb.utils、cb.extend）
- 生命周期事件（customInit、afterLoadData、beforeValidate、beforePush 等）
- 常见开发模式（单元格联动、参照过滤、代理调用、校验等）
- 业务场景（盘点流、新线资产流、清册验收流等）
- 8 个从简单到复杂的完整脚本示例

**触发场景：** 编写或修改 MDF 客开前端脚本、处理单据生命周期事件、操作 GridModel/FieldModel、调用后端 API 等。

## 开发规范

详见 [CLAUDE.md](./CLAUDE.md)。

### 创建新 Skill

1. 在 `skills/` 目录下创建新目录（kebab-case 命名）
2. 创建 `SKILL.md` 文件，包含：
    - YAML frontmatter（name 和 description）
    - Overview
    - When to Use
    - Quick Reference
    - Implementation
    - Common Mistakes
