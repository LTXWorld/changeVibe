import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


class ShellConfigManager:
    """管理 shell 配置文件（.zshrc 和 .bashrc）的修改"""

    def __init__(self):
        self.home = Path.home()
        self.zshrc = self.home / ".zshrc"
        self.bashrc = self.home / ".bashrc"

    def detect_shell_config(self) -> Optional[Path]:
        """检测当前使用的 shell 配置文件"""
        # 优先检查 zsh
        if self.zshrc.exists():
            return self.zshrc
        # 其次检查 bash
        if self.bashrc.exists():
            return self.bashrc
        return None

    def backup_config(self, config_file: Path) -> Path:
        """备份配置文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = config_file.parent / f"{config_file.name}.claude_switcher_backup_{timestamp}"
        shutil.copy2(config_file, backup_file)
        return backup_file

    def read_config(self, config_file: Path) -> str:
        """读取配置文件内容"""
        with open(config_file, 'r', encoding='utf-8') as f:
            return f.read()

    def write_config(self, config_file: Path, content: str):
        """写入配置文件"""
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def find_anthropic_block(self, content: str) -> Tuple[Optional[int], Optional[int]]:
        """
        查找 ANTHROPIC 相关配置块的起始和结束位置
        返回: (start_line, end_line) 或 (None, None)
        """
        lines = content.split('\n')
        start_line = None
        end_line = None

        for i, line in enumerate(lines):
            stripped = line.strip()
            # 查找 ANTHROPIC_AUTH_TOKEN
            if 'ANTHROPIC_AUTH_TOKEN' in stripped and stripped.startswith('export'):
                if start_line is None:
                    start_line = i
                end_line = i
            # 查找 ANTHROPIC_BASE_URL
            elif 'ANTHROPIC_BASE_URL' in stripped and stripped.startswith('export'):
                if start_line is None:
                    start_line = i
                end_line = i

        return start_line, end_line

    def remove_anthropic_config(self, content: str) -> str:
        """移除现有的 ANTHROPIC 配置"""
        lines = content.split('\n')
        new_lines = []

        for line in lines:
            stripped = line.strip()
            # 跳过 ANTHROPIC 相关的 export 语句
            if (stripped.startswith('export') and
                ('ANTHROPIC_AUTH_TOKEN' in stripped or 'ANTHROPIC_BASE_URL' in stripped)):
                continue
            new_lines.append(line)

        return '\n'.join(new_lines)

    def add_anthropic_config(self, content: str, token: str, base_url: str) -> str:
        """添加 ANTHROPIC 配置到文件末尾"""
        # 先移除旧配置
        content = self.remove_anthropic_config(content)

        # 确保文件末尾有空行
        if not content.endswith('\n'):
            content += '\n'

        # 添加注释和新配置
        config_block = f'''
# Claude Switcher: Claude Code API Configuration
export ANTHROPIC_AUTH_TOKEN="{token}"
export ANTHROPIC_BASE_URL="{base_url}"
'''
        return content + config_block

    def update_config(self, token: str, base_url: str, config_file: Optional[Path] = None) -> bool:
        """
        更新 shell 配置文件

        Args:
            token: API Token
            base_url: API Base URL
            config_file: 配置文件路径，如果为 None 则自动检测

        Returns:
            是否更新成功
        """
        if config_file is None:
            config_file = self.detect_shell_config()

        if config_file is None:
            print("错误: 未找到 .zshrc 或 .bashrc 文件")
            return False

        try:
            # 备份原文件
            backup_file = self.backup_config(config_file)
            print(f"已备份配置文件到: {backup_file}")

            # 读取原内容
            content = self.read_config(config_file)

            # 更新配置
            new_content = self.add_anthropic_config(content, token, base_url)

            # 写入新内容
            self.write_config(config_file, new_content)

            print(f"已更新配置文件: {config_file}")
            print(f"\n请执行以下命令使配置生效:")
            print(f"  source {config_file}")

            return True

        except Exception as e:
            print(f"更新配置文件时出错: {e}")
            return False

    def show_current_config(self, config_file: Optional[Path] = None) -> Optional[Tuple[str, str]]:
        """
        显示当前配置文件中的 ANTHROPIC 配置

        Returns:
            (token, base_url) 或 None
        """
        if config_file is None:
            config_file = self.detect_shell_config()

        if config_file is None:
            return None

        try:
            content = self.read_config(config_file)
            lines = content.split('\n')

            token = None
            base_url = None

            for line in lines:
                stripped = line.strip()
                if stripped.startswith('export') and 'ANTHROPIC_AUTH_TOKEN' in stripped:
                    # 提取 token 值
                    match = re.search(r'ANTHROPIC_AUTH_TOKEN="?([^"\s]+)"?', stripped)
                    if match:
                        token = match.group(1)
                elif stripped.startswith('export') and 'ANTHROPIC_BASE_URL' in stripped:
                    # 提取 base_url 值
                    match = re.search(r'ANTHROPIC_BASE_URL="?([^"\s]+)"?', stripped)
                    if match:
                        base_url = match.group(1)

            if token and base_url:
                return token, base_url

        except Exception as e:
            print(f"读取配置文件时出错: {e}")

        return None
