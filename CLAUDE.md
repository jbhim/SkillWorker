# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个个人 Claude Code Skills 仓库，用于管理和开发自定义技能。项目为纯文档型仓库，无构建/测试流程。

## 目录结构

```
skills/                                  # 所有 skill 的存放目录
  bailian-coding-plan/                   # 百炼模型切换 Skill
  configuring-opencode-providers/        # OpenCode 自定义供应商配置指南
  mdf-script-development/                # 用友 MDF 前端脚本开发 Skill
    ├── SKILL.md                         # 主入口文档
    ├── api-reference.md                 # 完整 API 参考
    ├── lifecycle-events.md              # 生命周期事件详解
    ├── common-patterns.md               # 常见开发模式
    ├── business-patterns.md             # 业务场景模式
    └── examples.md                      # 完整脚本示例
```

## 常用命令

```bash
# 查看已安装的 skills
npx skills list

# 安装本地 skill 到 Claude Code
npx skills add ./skills/<skill-name>

# 安装整个仓库
npx skills add ./skills

# 移除 skill
npx skills remove <skill-name>

# 重新加载 plugins
npx skills reload
```

## Skill 开发规范

### 目录命名

- 使用 kebab-case（短横线连接的小写字母）命名 skill 目录
- 名称应简洁描述 skill 的功能，使用动词开头
- 示例：`creating-skills`, `condition-based-waiting`, `root-cause-tracing`

### Skill 文件结构

每个 skill 目录必须包含：

```
skills/<skill-name>/
  ├── SKILL.md                    # 主文档（必需）
  └── supporting-file.*           # 支持文件（仅在需要时）
```

**SKILL.md 必需包含：**
- YAML frontmatter：`name` 和 `description` 字段（max 1024字符）
  - `name`: 仅使用字母、数字、连字符（无括号或特殊字符）
  - `description`: 以 "Use when..." 开头，描述触发条件（非功能描述）
- `## Overview` - 核心原则简述
- `## When to Use` - 使用场景和症状
- `## Quick Reference` - 快速参考表
- `## Implementation` - 实现细节或链接到支持文件

**支持文件仅在以下情况使用：**
- 重度参考资料（100+行）- API 文档、完整语法
- 可重用工具 - 脚本、工具、模板

### 记录语言

所有文档和注释使用中文记录。
