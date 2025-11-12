#!/usr/bin/env python3
"""
Vibe Switcher - Claude Code 和 Codex API 中转商切换工具
"""

import argparse
import sys
from claude_switcher.config import ConfigManager
from claude_switcher.shell import ShellConfigManager
from claude_switcher.codex import CodexConfigManager


# ==================== Claude Code 命令 ====================
def claude_list(args):
    """列出所有 Claude Code 中转商"""
    config_mgr = ConfigManager()
    providers = config_mgr.get_providers()
    current = config_mgr.get_current()

    if not providers:
        print("暂无配置的 Claude Code 中转商")
        return

    print("\n可用的 Claude Code 中转商:\n")
    for name, info in providers.items():
        marker = " ✓ (当前)" if name == current else ""
        print(f"  {name}{marker}")
        print(f"    URL: {info['base_url']}")
        if info['token']:
            token_display = info['token'][:10] + "..." + info['token'][-10:] if len(info['token']) > 20 else info['token']
            print(f"    Token: {token_display}")
        else:
            print(f"    Token: (未配置)")
        print()


def claude_switch(args):
    """切换 Claude Code 中转商"""
    config_mgr = ConfigManager()
    shell_mgr = ShellConfigManager()

    provider_name = args.provider
    provider = config_mgr.get_provider(provider_name)

    if not provider:
        print(f"错误: 未找到中转商 '{provider_name}'")
        print("\n请使用 'vibe-switcher claude list' 查看可用的中转商")
        return 1

    if not provider['token']:
        print(f"错误: 中转商 '{provider_name}' 的 Token 未配置")
        print(f"\n请使用以下命令配置 Token:")
        print(f"  vibe-switcher claude add {provider_name} <your-token> {provider['base_url']}")
        return 1

    success = shell_mgr.update_config(provider['token'], provider['base_url'])

    if success:
        config_mgr.set_current(provider_name)
        print(f"\n✓ 已切换到 Claude Code 中转商: {provider_name}")
        return 0
    else:
        return 1


def claude_add(args):
    """添加或更新 Claude Code 中转商配置"""
    config_mgr = ConfigManager()

    name = args.name
    token = args.token
    url = args.url

    config_mgr.add_provider(name, token, url)
    print(f"✓ 已添加/更新 Claude Code 中转商: {name}")
    print(f"  URL: {url}")
    print(f"  Token: {token[:10]}...{token[-10:] if len(token) > 20 else token}")


def claude_remove(args):
    """删除 Claude Code 中转商配置"""
    config_mgr = ConfigManager()

    name = args.name

    if config_mgr.remove_provider(name):
        print(f"✓ 已删除 Claude Code 中转商: {name}")
        return 0
    else:
        print(f"错误: 未找到中转商 '{name}'")
        return 1


def claude_current(args):
    """显示当前 Claude Code 配置"""
    config_mgr = ConfigManager()
    shell_mgr = ShellConfigManager()

    current_name = config_mgr.get_current()
    current_provider = config_mgr.get_current_provider()

    print("\n当前 Claude Code 配置:\n")

    if current_name and current_provider:
        print(f"  中转商: {current_name}")
        print(f"  URL: {current_provider['base_url']}")
        if current_provider['token']:
            token_display = current_provider['token'][:10] + "..." + current_provider['token'][-10:] \
                if len(current_provider['token']) > 20 else current_provider['token']
            print(f"  Token: {token_display}")
    else:
        print("  (未设置)")

    print("\nShell 配置文件中的值:\n")
    shell_config = shell_mgr.show_current_config()
    if shell_config:
        token, base_url = shell_config
        token_display = token[:10] + "..." + token[-10:] if len(token) > 20 else token
        print(f"  ANTHROPIC_AUTH_TOKEN: {token_display}")
        print(f"  ANTHROPIC_BASE_URL: {base_url}")

        if current_provider:
            if token != current_provider['token'] or base_url != current_provider['base_url']:
                print("\n⚠️  警告: Shell 配置与当前中转商不一致")
                print("   请运行 'vibe-switcher claude switch <provider>' 来更新配置")
    else:
        print("  (未配置)")

    config_file = shell_mgr.detect_shell_config()
    if config_file:
        print(f"\n配置文件: {config_file}")


# ==================== Codex 命令 ====================
def codex_list(args):
    """列出所有 Codex 中转商"""
    config_mgr = ConfigManager()
    providers = config_mgr.get_codex_providers()
    current = config_mgr.get_current_codex()

    if not providers:
        print("暂无配置的 Codex 中转商")
        return

    print("\n可用的 Codex 中转商:\n")
    for name, info in providers.items():
        marker = " ✓ (当前)" if name == current else ""
        print(f"  {name}{marker}")
        print(f"    URL: {info['base_url']}")
        if info.get('network_access'):
            print(f"    Network Access: {info['network_access']}")
        if info['api_key']:
            key_display = info['api_key'][:10] + "..." + info['api_key'][-10:] if len(info['api_key']) > 20 else info['api_key']
            print(f"    API Key: {key_display}")
        else:
            print(f"    API Key: (未配置)")
        print()


def codex_switch(args):
    """切换 Codex 中转商"""
    config_mgr = ConfigManager()
    codex_mgr = CodexConfigManager()

    provider_name = args.provider
    provider = config_mgr.get_codex_provider(provider_name)

    if not provider:
        print(f"错误: 未找到 Codex 中转商 '{provider_name}'")
        print("\n请使用 'vibe-switcher codex list' 查看可用的中转商")
        return 1

    if not provider['api_key']:
        print(f"错误: Codex 中转商 '{provider_name}' 的 API Key 未配置")
        print(f"\n请使用以下命令配置 API Key:")
        print(f"  vibe-switcher codex add {provider_name} <your-api-key> {provider['base_url']}")
        if provider.get('network_access'):
            print(f"  # network_access: {provider['network_access']}")
        return 1

    success = codex_mgr.update_codex_config(provider_name, provider, provider['api_key'])

    if success:
        config_mgr.set_current_codex(provider_name)
        print(f"\n✓ 已切换到 Codex 中转商: {provider_name}")
        return 0
    else:
        return 1


def codex_add(args):
    """添加或更新 Codex 中转商配置"""
    config_mgr = ConfigManager()

    name = args.name
    api_key = args.api_key
    url = args.url
    network_access = args.network_access if hasattr(args, 'network_access') and args.network_access else ""

    config_mgr.add_codex_provider(name, api_key, url, network_access)
    print(f"✓ 已添加/更新 Codex 中转商: {name}")
    print(f"  URL: {url}")
    print(f"  API Key: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
    if network_access:
        print(f"  Network Access: {network_access}")


def codex_remove(args):
    """删除 Codex 中转商配置"""
    config_mgr = ConfigManager()

    name = args.name

    if config_mgr.remove_codex_provider(name):
        print(f"✓ 已删除 Codex 中转商: {name}")
        return 0
    else:
        print(f"错误: 未找到 Codex 中转商 '{name}'")
        return 1


def codex_current(args):
    """显示当前 Codex 配置"""
    config_mgr = ConfigManager()
    codex_mgr = CodexConfigManager()

    current_name = config_mgr.get_current_codex()
    current_provider = config_mgr.get_current_codex_provider()

    print("\n当前 Codex 配置:\n")

    if current_name and current_provider:
        print(f"  中转商: {current_name}")
        print(f"  URL: {current_provider['base_url']}")
        if current_provider.get('network_access'):
            print(f"  Network Access: {current_provider['network_access']}")
        if current_provider['api_key']:
            key_display = current_provider['api_key'][:10] + "..." + current_provider['api_key'][-10:] \
                if len(current_provider['api_key']) > 20 else current_provider['api_key']
            print(f"  API Key: {key_display}")
    else:
        print("  (未设置)")

    print("\nCodex 配置文件中的值:\n")
    codex_config = codex_mgr.show_current_config()
    if codex_config:
        print(f"  Provider: {codex_config['provider']}")
        print(f"  Base URL: {codex_config['base_url']}")
        if codex_config['api_key']:
            key_display = codex_config['api_key'][:10] + "..." + codex_config['api_key'][-10:] \
                if len(codex_config['api_key']) > 20 else codex_config['api_key']
            print(f"  API Key: {key_display}")

        if current_provider:
            if (codex_config['api_key'] != current_provider['api_key'] or
                codex_config['base_url'] != current_provider['base_url']):
                print("\n⚠️  警告: Codex 配置与当前中转商不一致")
                print("   请运行 'vibe-switcher codex switch <provider>' 来更新配置")
    else:
        print("  (未配置)")

    print(f"\n配置文件:")
    print(f"  config.toml: {codex_mgr.config_toml}")
    print(f"  auth.json: {codex_mgr.auth_json}")


# ==================== 主程序 ====================
def main():
    parser = argparse.ArgumentParser(
        description="Vibe Switcher - Claude Code 和 Codex API 中转商切换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # Claude Code 操作
  vibe-switcher claude list                    # 列出所有 Claude Code 中转商
  vibe-switcher claude switch duck             # 切换到 duck 中转商
  vibe-switcher claude add fox <token> <url>   # 添加中转商
  vibe-switcher claude remove fox              # 删除中转商
  vibe-switcher claude current                 # 查看当前配置

  # Codex 操作
  vibe-switcher codex list                     # 列出所有 Codex 中转商
  vibe-switcher codex switch duck              # 切换到 duck 中转商
  vibe-switcher codex add fox <key> <url>      # 添加中转商
  vibe-switcher codex remove fox               # 删除中转商
  vibe-switcher codex current                  # 查看当前配置
        """
    )

    subparsers = parser.add_subparsers(dest='service', help='选择服务类型')

    # ==================== Claude Code 子命令 ====================
    claude_parser = subparsers.add_parser('claude', help='Claude Code 相关操作')
    claude_subparsers = claude_parser.add_subparsers(dest='action', help='操作类型')

    # claude list
    claude_list_parser = claude_subparsers.add_parser(
        'list',
        help='列出所有 Claude Code 中转商',
        description='列出所有已配置的 Claude Code 中转商，并显示当前正在使用的中转商'
    )
    claude_list_parser.set_defaults(func=claude_list)

    # claude switch
    claude_switch_parser = claude_subparsers.add_parser(
        'switch',
        help='切换 Claude Code 中转商: switch <provider>',
        description='切换到指定的 Claude Code 中转商',
        usage='vibe-switcher claude switch <provider>'
    )
    claude_switch_parser.add_argument('provider', metavar='<provider>', help='要切换到的中转商名称')
    claude_switch_parser.set_defaults(func=claude_switch)

    # claude add
    claude_add_parser = claude_subparsers.add_parser(
        'add',
        help='添加或更新 Claude Code 中转商: add <name> <token> <url>',
        description='添加新的 Claude Code 中转商配置，或更新已存在的中转商配置',
        usage='vibe-switcher claude add <name> <token> <url>'
    )
    claude_add_parser.add_argument('name', metavar='<name>', help='中转商名称（标识符）')
    claude_add_parser.add_argument('token', metavar='<token>', help='API Token（用于认证）')
    claude_add_parser.add_argument('url', metavar='<url>', help='API Base URL（中转商的接口地址）')
    claude_add_parser.set_defaults(func=claude_add)

    # claude remove
    claude_remove_parser = claude_subparsers.add_parser(
        'remove',
        help='删除 Claude Code 中转商: remove <name>',
        description='从配置中删除指定的 Claude Code 中转商',
        usage='vibe-switcher claude remove <name>'
    )
    claude_remove_parser.add_argument('name', metavar='<name>', help='要删除的中转商名称')
    claude_remove_parser.set_defaults(func=claude_remove)

    # claude current
    claude_current_parser = claude_subparsers.add_parser(
        'current',
        help='显示当前 Claude Code 配置',
        description='显示当前正在使用的 Claude Code 中转商配置，包括配置文件中的实际值'
    )
    claude_current_parser.set_defaults(func=claude_current)

    # ==================== Codex 子命令 ====================
    codex_parser = subparsers.add_parser('codex', help='Codex 相关操作')
    codex_subparsers = codex_parser.add_subparsers(dest='action', help='操作类型')

    # codex list
    codex_list_parser = codex_subparsers.add_parser(
        'list',
        help='列出所有 Codex 中转商',
        description='列出所有已配置的 Codex 中转商，并显示当前正在使用的中转商'
    )
    codex_list_parser.set_defaults(func=codex_list)

    # codex switch
    codex_switch_parser = codex_subparsers.add_parser(
        'switch',
        help='切换 Codex 中转商: switch <provider>',
        description='切换到指定的 Codex 中转商',
        usage='vibe-switcher codex switch <provider>'
    )
    codex_switch_parser.add_argument('provider', metavar='<provider>', help='要切换到的中转商名称')
    codex_switch_parser.set_defaults(func=codex_switch)

    # codex add
    codex_add_parser = codex_subparsers.add_parser(
        'add',
        help='添加或更新 Codex 中转商: add <name> <api_key> <url> [--network-access <value>]',
        description='添加新的 Codex 中转商配置，或更新已存在的中转商配置',
        usage='vibe-switcher codex add <name> <api_key> <url> [--network-access <value>]'
    )
    codex_add_parser.add_argument('name', metavar='<name>', help='中转商名称（标识符）')
    codex_add_parser.add_argument('api_key', metavar='<api_key>', help='API Key（用于认证）')
    codex_add_parser.add_argument('url', metavar='<url>', help='API Base URL（中转商的接口地址）')
    codex_add_parser.add_argument('--network-access', metavar='<value>', help='Network Access 设置（可选，如 "enabled" 或 "disabled"）', default="")
    codex_add_parser.set_defaults(func=codex_add)

    # codex remove
    codex_remove_parser = codex_subparsers.add_parser(
        'remove',
        help='删除 Codex 中转商: remove <name>',
        description='从配置中删除指定的 Codex 中转商',
        usage='vibe-switcher codex remove <name>'
    )
    codex_remove_parser.add_argument('name', metavar='<name>', help='要删除的中转商名称')
    codex_remove_parser.set_defaults(func=codex_remove)

    # codex current
    codex_current_parser = codex_subparsers.add_parser(
        'current',
        help='显示当前 Codex 配置',
        description='显示当前正在使用的 Codex 中转商配置，包括配置文件中的实际值'
    )
    codex_current_parser.set_defaults(func=codex_current)

    # 解析参数
    args = parser.parse_args()

    # 如果没有指定服务类型，显示帮助信息
    if not args.service:
        parser.print_help()
        return 0

    # 如果没有指定操作，显示对应服务的帮助
    if not hasattr(args, 'func'):
        if args.service == 'claude':
            claude_parser.print_help()
        elif args.service == 'codex':
            codex_parser.print_help()
        return 0

    # 执行对应的命令
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
