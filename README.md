# Vibe Switcher

Claude Code 和 Codex API 中转商切换工具 - 在命令行中快速切换不同的 API 中转服务。

## 功能特性

- 🚀 支持 Claude Code 和 Codex 两种服务的中转商切换
- 🔧 Claude Code: 自动修改 `.zshrc` 和 `.bashrc` 配置文件
- 📝 Codex: 自动修改 `.codex/config.toml` 和 `.codex/auth.json`
- 💾 支持多个中转商配置管理
- 🔒 自动备份配置文件
- 📋 内置主流中转商配置
- 🎯 两级命令结构，操作清晰直观

## 安装

### 方法 1: 使用 pip 安装（推荐）

```bash
pip install -e .
```

### 方法 2: 使用安装脚本

```bash
./install.sh
```

### 方法 3: 直接运行

```bash
python3 claude_switcher/cli.py <command>
```

## 命令结构

Vibe Switcher 使用两级命令结构：

```
vibe-switcher <服务类型> <操作> [参数]
```

- **服务类型**: `claude` (Claude Code) 或 `codex` (Codex)
- **操作**: `list`, `switch`, `add`, `remove`/`delete`, `current`

## 快速开始

### Claude Code 操作

#### 1. 查看所有 Claude Code 中转商

```bash
vibe-switcher claude list
```

#### 2. 配置 Claude Code 中转商 Token

默认提供 4 个中转商，但需要配置各自的 Token：

```bash
# 配置 fox 中转商
vibe-switcher claude add fox sk-your-token-here https://code.newcli.com/claude

# 配置 duck 中转商
vibe-switcher claude add duck sk-your-token-here https://jp.instcopilot-api.com

# 配置 88code 中转商
vibe-switcher claude add 88code sk-your-token-here https://www.88code.org/api

# 配置 packy 中转商
vibe-switcher claude add packy sk-your-token-here https://api.packycode.com
```

#### 3. 切换 Claude Code 中转商

```bash
vibe-switcher claude switch fox
```

切换后会自动修改你的 shell 配置文件（`.zshrc` 或 `.bashrc`），并提示你执行 `source` 命令使配置生效。

#### 4. 查看当前 Claude Code 配置

```bash
vibe-switcher claude current
```

### Codex 操作

#### 1. 查看所有 Codex 中转商

```bash
vibe-switcher codex list
```

#### 2. 配置 Codex 中转商 API Key

```bash
# 配置 duck 中转商（带 network access）
vibe-switcher codex add duck sk-your-api-key https://jp.duckcoding.com/v1 --network-access enabled

# 配置 fox 中转商
vibe-switcher codex add fox sk-your-api-key https://code.newcli.com/codex/v1
```

#### 3. 切换 Codex 中转商

```bash
vibe-switcher codex switch duck
```

切换后会自动修改 `~/.codex/config.toml` 和 `~/.codex/auth.json` 文件。

#### 4. 查看当前 Codex 配置

```bash
vibe-switcher codex current
```

## 命令详解

### Claude Code 命令

#### `vibe-switcher claude list`
列出所有已配置的 Claude Code 中转商，包括 URL 和 Token 信息（已脱敏显示）。

#### `vibe-switcher claude switch <provider>`
切换到指定的 Claude Code 中转商，自动更新 shell 配置文件中的环境变量：
- `ANTHROPIC_AUTH_TOKEN`
- `ANTHROPIC_BASE_URL`

**示例**:
```bash
vibe-switcher claude switch duck
source ~/.zshrc  # 使配置生效
```

#### `vibe-switcher claude add <name> <token> <url>`
添加新的 Claude Code 中转商或更新现有中转商的配置。

**示例**:
```bash
vibe-switcher claude add myapi sk-abc123 https://my-api.com
```

#### `vibe-switcher claude remove <name>`
从配置中删除指定的 Claude Code 中转商。

**示例**:
```bash
vibe-switcher claude remove myapi
```

#### `vibe-switcher claude current`
显示当前激活的 Claude Code 中转商信息，以及 shell 配置文件中的实际值。

### Codex 命令

#### `vibe-switcher codex list`
列出所有已配置的 Codex 中转商，包括 URL、API Key 和 Network Access 信息。

#### `vibe-switcher codex switch <provider>`
切换到指定的 Codex 中转商，自动更新：
- `~/.codex/config.toml`
- `~/.codex/auth.json`

**示例**:
```bash
vibe-switcher codex switch fox
```

#### `vibe-switcher codex add <name> <api_key> <url> [--network-access <value>]`
添加新的 Codex 中转商或更新现有中转商的配置。

**参数**:
- `name`: 中转商名称
- `api_key`: API Key
- `url`: API Base URL
- `--network-access`: (可选) 网络访问设置，如 `enabled`

**示例**:
```bash
vibe-switcher codex add duck sk-abc123 https://jp.duckcoding.com/v1 --network-access enabled
```

#### `vibe-switcher codex remove <name>`
从配置中删除指定的 Codex 中转商。

**示例**:
```bash
vibe-switcher codex remove duck
```

#### `vibe-switcher codex current`
显示当前激活的 Codex 中转商信息，以及 Codex 配置文件中的实际值。

#### 特定服务商适配
为避免不同中转商的配置差异导致手动修改，这里内置了针对常见服务商的适配逻辑：

- **duck**: 自动写入 `requires_openai_auth = true` 与 `disable_response_storage = true`，并在 `auth.json` 中仅保留 `OPENAI_API_KEY`。
- **yescode**: 自动补充 `env_key = "YESCODE_API_KEY"`、为当前命令执行目录添加 `trust_level = "trusted"` 的项目配置，同时在 `auth.json` 中写入 `OPENAI_API_KEY` 与 `YESCODE_API_KEY` 两个字段。若需要为多个项目授权，可在 `~/.config/claude-switcher/config.json` 的 `codex_providers.yescode.projects` 中添加更多路径。

## 配置文件

### Claude Code 配置

**配置文件位置**: `~/.config/claude-switcher/config.json`

**配置文件结构**:
```json
{
  "providers": {
    "fox": {
      "token": "sk-xxx",
      "base_url": "https://code.newcli.com/claude"
    },
    "duck": {
      "token": "sk-yyy",
      "base_url": "https://jp.instcopilot-api.com"
    }
  },
  "current": "duck",
  "env_vars": {
    "token": "ANTHROPIC_AUTH_TOKEN",
    "base_url": "ANTHROPIC_BASE_URL"
  }
}
```

### Codex 配置

**配置文件位置**: `~/.config/claude-switcher/config.json`

**Codex 部分结构**:
```json
{
  "codex_providers": {
    "fox": {
      "api_key": "sk-xxx",
      "base_url": "https://code.newcli.com/codex/v1",
      "network_access": ""
    },
    "duck": {
      "api_key": "sk-yyy",
      "base_url": "https://jp.duckcoding.com/v1",
      "network_access": "enabled"
    }
  },
  "current_codex": "duck"
}
```

**Codex 运行时配置**:
- `~/.codex/config.toml` - Codex 主配置文件（TOML 格式）
- `~/.codex/auth.json` - Codex 认证文件（JSON 格式）

## 备份机制

### Claude Code 备份
每次修改 shell 配置文件前，工具会自动创建备份：
```
~/.zshrc.claude_switcher_backup_20241002_153045
```

### Codex 备份
每次修改 Codex 配置前，工具会自动创建备份：
```
~/.codex/config.toml.claude_switcher_backup_20241002_153045
~/.codex/auth.json.claude_switcher_backup_20241002_153045
```

备份文件名包含时间戳，便于恢复。

## 内置中转商

### Claude Code 中转商

| 名称 | URL |
|------|-----|
| fox | https://code.newcli.com/claude |
| duck | https://jp.instcopilot-api.com |
| 88code | https://www.88code.org/api |
| packy | https://api.packycode.com |

### Codex 中转商

| 名称 | URL | Network Access |
|------|-----|----------------|
| fox | https://code.newcli.com/codex/v1 | - |
| duck | https://jp.duckcoding.com/v1 | enabled |

## 使用场景

### 场景 1: 首次配置 Claude Code

```bash
# 1. 安装工具
pip install -e .

# 2. 配置你的 Token
vibe-switcher claude add duck sk-your-token-here https://jp.instcopilot-api.com

# 3. 切换到该中转商
vibe-switcher claude switch duck

# 4. 使配置生效
source ~/.zshrc  # 或 source ~/.bashrc
```

### 场景 2: 切换 Claude Code 中转商

```bash
# 查看可用的中转商
vibe-switcher claude list

# 切换到另一个中转商
vibe-switcher claude switch fox

# 使配置生效
source ~/.zshrc
```

### 场景 3: 配置和切换 Codex

```bash
# 配置 Codex 中转商
vibe-switcher codex add duck sk-your-api-key https://jp.duckcoding.com/v1 --network-access enabled

# 切换 Codex 中转商
vibe-switcher codex switch duck

# 查看当前配置
vibe-switcher codex current
```

### 场景 4: 同时管理两种服务

```bash
# 切换 Claude Code 到 fox
vibe-switcher claude switch fox
source ~/.zshrc

# 切换 Codex 到 duck
vibe-switcher codex switch duck

# 查看两者的当前配置
vibe-switcher claude current
vibe-switcher codex current
```

## 支持的 Shell

### Claude Code
- ✅ Zsh (`.zshrc`)
- ✅ Bash (`.bashrc`)

工具会自动检测你当前使用的 shell 配置文件。

### Codex
- ✅ 所有 Shell（通过修改 `~/.codex/` 配置文件）

## 注意事项

### Claude Code
1. **Token 安全**: 配置文件权限自动设置为 600（仅所有者可读写）
2. **备份恢复**: 如需恢复配置，可从备份文件中复制内容
3. **配置生效**: 修改后需要执行 `source ~/.zshrc` 或重启终端
4. **多终端**: 已打开的终端需要重新 source 配置文件

### Codex
1. **配置文件**: 自动管理 TOML 和 JSON 格式的配置
2. **备份恢复**: 两个配置文件都会自动备份
3. **Network Access**: 可选配置，部分中转商需要设置为 `enabled`

## 开发

### 项目结构

```
vibe-switcher/
├── claude_switcher/
│   ├── __init__.py      # 包初始化
│   ├── cli.py           # CLI 入口（两级命令结构）
│   ├── config.py        # 配置管理（Claude Code + Codex）
│   ├── shell.py         # Shell 配置文件处理（zsh/bash）
│   └── codex.py         # Codex 配置文件处理（TOML/JSON）
├── pyproject.toml       # 项目配置
├── install.sh           # 安装脚本
├── README.md            # 说明文档
└── IMPLEMENTATION_PLAN.md  # 实现计划
```

### 本地开发

```bash
# 以可编辑模式安装
pip install -e .

# 查看帮助
vibe-switcher --help
vibe-switcher claude --help
vibe-switcher codex --help
```

### 技术栈

- **Python 3.7+**
- **argparse** - 命令行参数解析（两级子命令）
- **json** - JSON 配置管理
- **pathlib** - 文件路径操作
- **shutil** - 文件备份

## 常见问题

### Q: 如何查看当前使用的是哪个中转商？
```bash
vibe-switcher claude current  # Claude Code
vibe-switcher codex current   # Codex
```

### Q: 切换后配置不生效怎么办？
**Claude Code**: 执行 `source ~/.zshrc` 或 `source ~/.bashrc`
**Codex**: 配置立即生效，无需额外操作

### Q: 如何恢复到之前的配置？
查看备份文件（文件名包含时间戳），从备份文件中复制内容恢复。

### Q: 可以同时使用不同的 Claude Code 和 Codex 中转商吗？
可以。两种服务的配置是独立的，互不影响。

### Q: 如何添加自定义中转商？
```bash
# Claude Code
vibe-switcher claude add myservice sk-token-123 https://my-api.com

# Codex
vibe-switcher codex add myservice sk-key-456 https://my-codex-api.com
```

## License

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！
