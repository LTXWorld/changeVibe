#!/bin/bash

# Vibe Switcher 安装脚本

echo "开始安装 Vibe Switcher..."

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "检测到 Python 版本: $PYTHON_VERSION"

# 检查是否在项目目录中
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 请在项目根目录中运行此脚本"
    exit 1
fi

# 安装包
echo "正在安装 Vibe Switcher..."
pip3 install -e .

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Vibe Switcher 安装成功！"
    echo ""
    echo "快速开始:"
    echo ""
    echo "  Claude Code 操作:"
    echo "    vibe-switcher claude list                    # 列出所有中转商"
    echo "    vibe-switcher claude add duck <token> <url>  # 配置中转商"
    echo "    vibe-switcher claude switch duck             # 切换中转商"
    echo "    vibe-switcher claude current                 # 查看当前配置"
    echo "    source ~/.zshrc                              # 使配置生效"
    echo ""
    echo "  Codex 操作:"
    echo "    vibe-switcher codex list                     # 列出所有中转商"
    echo "    vibe-switcher codex add duck <key> <url>     # 配置中转商"
    echo "    vibe-switcher codex switch duck              # 切换中转商"
    echo "    vibe-switcher codex current                  # 查看当前配置"
    echo ""
    echo "  查看帮助:"
    echo "    vibe-switcher --help"
    echo "    vibe-switcher claude --help"
    echo "    vibe-switcher codex --help"
    echo ""
else
    echo "安装失败，请检查错误信息"
    exit 1
fi
