# Vibe Switcher 实现计划

## 项目概述
命令行工具，用于快速切换不同的 Claude Code 和 Codex API 中转商配置。

## 已完成功能

### ✅ Stage 1: 项目结构和配置文件（已完成）
**Goal**: 建立基础项目结构和默认配置
**Success Criteria**:
- ✅ 项目目录结构完整
- ✅ 默认配置包含 Claude Code 中转商（fox, duck, 88code, packy）
- ✅ 默认配置包含 Codex 中转商（fox, duck）
- ✅ 配置文件模板就绪
**Status**: Completed

### ✅ Stage 2: 配置管理模块（已完成）
**Goal**: 实现配置文件的读写和管理
**Success Criteria**:
- ✅ 读取/写入配置文件
- ✅ 添加/删除/列出 Claude Code 中转商
- ✅ 添加/删除/列出 Codex 中转商
- ✅ 获取当前激活的中转商
**Status**: Completed

### ✅ Stage 3: Shell 配置文件修改功能（已完成）
**Goal**: 安全修改 .zshrc 和 .bashrc 文件
**Success Criteria**:
- ✅ 识别并替换 ANTHROPIC_AUTH_TOKEN 和 ANTHROPIC_BASE_URL
- ✅ 支持 zsh 和 bash
- ✅ 自动备份原文件
- ✅ 保留其他配置不变
**Status**: Completed

### ✅ Stage 4: Codex 配置文件支持（已完成）
**Goal**: 支持 Codex 的 TOML 和 JSON 配置文件
**Success Criteria**:
- ✅ 生成和修改 config.toml（TOML 格式）
- ✅ 生成和修改 auth.json（JSON 格式）
- ✅ 自动备份 Codex 配置文件
- ✅ 支持 network_access 等可选参数
**Status**: Completed

### ✅ Stage 5: CLI 两级命令接口（已完成）
**Goal**: 用户友好的两级命令行界面
**Success Criteria**:
- ✅ `vibe-switcher claude <action>` - Claude Code 操作
- ✅ `vibe-switcher codex <action>` - Codex 操作
- ✅ `list` - 列出所有配置
- ✅ `switch <provider>` - 切换中转商
- ✅ `add <name> <token/key> <url>` - 添加新中转商
- ✅ `remove <name>` - 删除中转商
- ✅ `current` - 显示当前配置
**Status**: Completed

### ✅ Stage 6: 安装脚本和文档（已完成）
**Goal**: 简化安装和使用
**Success Criteria**:
- ✅ pyproject.toml 配置
- ✅ 安装脚本
- ✅ 完整的 README 使用说明
- ✅ 可通过 pip 安装
**Status**: Completed

## 技术架构

### 技术栈
- **Python 3.7+**
- **argparse** - 两级 CLI 命令解析
- **json** - JSON 配置存储
- **pathlib** - 文件路径操作
- **shutil** - 文件备份
- **TOML** - Codex 配置格式（字符串生成）

### 项目结构
```
vibe-switcher/
├── claude_switcher/
│   ├── __init__.py      # 包初始化
│   ├── cli.py           # CLI 入口（两级命令）
│   ├── config.py        # 配置管理（Claude Code + Codex）
│   ├── shell.py         # Shell 配置文件处理
│   └── codex.py         # Codex 配置文件处理（TOML/JSON）
├── pyproject.toml       # 项目配置
├── install.sh           # 安装脚本
├── README.md            # 完整文档
└── IMPLEMENTATION_PLAN.md  # 本文件
```

## 配置文件

### 主配置文件位置
`~/.config/claude-switcher/config.json`

### Claude Code 配置
- **环境变量**: `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`
- **配置文件**: `~/.zshrc` 或 `~/.bashrc`
- **备份格式**: `.zshrc.claude_switcher_backup_<timestamp>`

### Codex 配置
- **运行时配置**:
  - `~/.codex/config.toml` (TOML 格式)
  - `~/.codex/auth.json` (JSON 格式)
- **备份格式**:
  - `config.toml.claude_switcher_backup_<timestamp>`
  - `auth.json.claude_switcher_backup_<timestamp>`

## 内置中转商

### Claude Code
- fox: https://code.newcli.com/claude
- duck: https://jp.instcopilot-api.com
- 88code: https://www.88code.org/api
- packy: https://api.packycode.com

### Codex
- fox: https://code.newcli.com/codex/v1
- duck: https://jp.duckcoding.com/v1 (network_access: enabled)

## 命令示例

### Claude Code
```bash
vibe-switcher claude list
vibe-switcher claude switch duck
vibe-switcher claude add myapi <token> <url>
vibe-switcher claude current
vibe-switcher claude remove myapi
```

### Codex
```bash
vibe-switcher codex list
vibe-switcher codex switch duck
vibe-switcher codex add myapi <key> <url> --network-access enabled
vibe-switcher codex current
vibe-switcher codex remove myapi
```

## 未来扩展

### 可能的功能
- [ ] 支持更多 shell（fish, powershell）
- [ ] 配置文件加密
- [ ] 从环境变量导入当前配置
- [ ] 交互式配置向导
- [ ] 配置文件验证
- [ ] 批量切换（同时切换 Claude Code 和 Codex）

## 版本历史

- **v0.1.0**: 初始版本，支持 Claude Code
- **v0.2.0**: 添加 Codex 支持，重构为两级命令结构

## 测试清单

- [x] Claude Code 配置读写
- [x] Codex 配置读写
- [x] Shell 文件修改和备份
- [x] Codex TOML/JSON 生成和备份
- [x] CLI 命令解析（两级结构）
- [x] 中转商切换功能
- [x] 配置显示功能
- [x] pip 安装
- [x] 多中转商管理
- [x] 错误处理和用户提示
