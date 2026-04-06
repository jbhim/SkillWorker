# MySkillWorker

个人 Claude Code Skills 开发仓库，用于管理和开发自定义技能。

## 项目结构

```
.
├── CLAUDE.md                   # 项目开发规范
├── README.md                   # 本文件
└── skills/                     # Skill 目录
    └── bailian-coding-plan/    # 百炼模型切换 Skill
        └── SKILL.md
```

## 使用方法

### 安装 Skills 到 Claude Code

将本项目的 skills 安装到 Claude Code 中：

```bash
npx skills add ./skills
```

或安装单个 skill：

```bash
npx skills add ./skills/bailian-coding-plan
```

### 使用 Skill

安装完成后，在 Claude Code 中使用：

```bash
/skill bailian-coding-plan
```

## Skill 列表

### bailian-coding-plan

切换 Claude Code 模型至阿里云百炼平台的大语言模型。

**支持的模型：**

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

**配置方式：**

修改 `~/.claude/settings.json` 中的 `env.ANTHROPIC_MODEL` 字段：

```json
{
  "env": {
    "ANTHROPIC_MODEL": "qwen3.5-plus"
  }
}
```

重启 Claude Code 后生效。

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

### Skill 目录结构

```
skills/<skill-name>/
  ├── SKILL.md              # 主文档（必需）
  └── supporting-file.*     # 支持文件（仅在需要时）
```

## 相关命令

```bash
# 查看已安装的 skills
npx skills list

# 安装本地 skill
npx skills add ./skills/<skill-name>

# 移除 skill
npx skills remove <skill-name>

# 重新加载 plugins
npx skills reload
```
