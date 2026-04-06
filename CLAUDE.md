# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个专门用于开发 Claude Code Skills 的项目，目前处于起步阶段。

## 目录结构

```
skills/                           # 所有 skill 的存放目录
  <skill-name>/                   # skill 目录（kebab-case命名）
    ├── SKILL.md                  # 主文档（必需）
    └── supporting-file.*         # 支持文件（仅在需要时）
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
