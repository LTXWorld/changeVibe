import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class CodexConfigManager:
    """管理 Codex 配置文件（config.toml 和 auth.json）的修改"""

    def __init__(self):
        self.home = Path.home()
        self.codex_dir = self.home / ".codex"
        self.config_toml = self.codex_dir / "config.toml"
        self.auth_json = self.codex_dir / "auth.json"

    def _ensure_codex_dir(self):
        """确保 .codex 目录存在"""
        self.codex_dir.mkdir(parents=True, exist_ok=True)

    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = file_path.parent / f"{file_path.name}.claude_switcher_backup_{timestamp}"
        if file_path.exists():
            shutil.copy2(file_path, backup_file)
        return backup_file

    def read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def write_file(self, file_path: Path, content: str):
        """写入文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def generate_config_toml(self, provider_name: str, provider_config: Dict) -> str:
        """
        生成 config.toml 内容

        Args:
            provider_name: 中转商名称
            provider_config: 中转商配置信息
        """
        toml_content = f'''model_provider = "{provider_name}"
model = "gpt-5-codex"
model_reasoning_effort = "high"
'''

        # 添加可选配置
        if provider_config.get('network_access'):
            toml_content += f'network_access = "{provider_config["network_access"]}"\n'

        toml_content += 'disable_response_storage = true\n\n'

        # 添加 model_providers 配置
        toml_content += f'[model_providers.{provider_name}]\n'
        toml_content += f'name = "{provider_name}"\n'
        toml_content += f'base_url = "{provider_config["base_url"]}"\n'
        toml_content += f'wire_api = "responses"\n'
        toml_content += f'requires_openai_auth = true\n'

        return toml_content

    def update_auth_json(self, api_key: str):
        """更新 auth.json 文件"""
        auth_data = {
            "OPENAI_API_KEY": api_key
        }

        with open(self.auth_json, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f, indent=2, ensure_ascii=False)

    def update_codex_config(self, provider_name: str, provider_config: Dict, api_key: str) -> bool:
        """
        更新 Codex 配置

        Args:
            provider_name: 中转商名称
            provider_config: 中转商配置（base_url, network_access 等）
            api_key: API Key

        Returns:
            是否更新成功
        """
        try:
            self._ensure_codex_dir()

            # 备份 config.toml
            if self.config_toml.exists():
                backup_file = self.backup_file(self.config_toml)
                print(f"已备份 config.toml 到: {backup_file}")

            # 备份 auth.json
            if self.auth_json.exists():
                backup_file = self.backup_file(self.auth_json)
                print(f"已备份 auth.json 到: {backup_file}")

            # 生成并写入新的 config.toml
            toml_content = self.generate_config_toml(provider_name, provider_config)
            self.write_file(self.config_toml, toml_content)
            print(f"已更新配置文件: {self.config_toml}")

            # 更新 auth.json
            self.update_auth_json(api_key)
            print(f"已更新认证文件: {self.auth_json}")

            return True

        except Exception as e:
            print(f"更新 Codex 配置时出错: {e}")
            return False

    def show_current_config(self) -> Optional[Dict]:
        """
        显示当前 Codex 配置

        Returns:
            包含 provider, base_url, api_key 的字典，或 None
        """
        try:
            if not self.config_toml.exists():
                return None

            config_content = self.read_file(self.config_toml)

            # 简单解析 TOML（提取关键信息）
            provider_name = None
            base_url = None

            for line in config_content.split('\n'):
                line = line.strip()
                if line.startswith('model_provider ='):
                    provider_name = line.split('=')[1].strip().strip('"')
                elif line.startswith('base_url ='):
                    base_url = line.split('=')[1].strip().strip('"')

            # 读取 API Key
            api_key = None
            if self.auth_json.exists():
                with open(self.auth_json, 'r', encoding='utf-8') as f:
                    auth_data = json.load(f)
                    api_key = auth_data.get('OPENAI_API_KEY')

            if provider_name and base_url:
                return {
                    'provider': provider_name,
                    'base_url': base_url,
                    'api_key': api_key
                }

        except Exception as e:
            print(f"读取 Codex 配置时出错: {e}")

        return None
