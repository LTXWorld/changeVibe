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

    def _detect_project_path(self) -> str:
        """检测当前项目路径，默认取调用命令时的工作目录"""
        try:
            return str(Path.cwd())
        except Exception:
            return str(self.home)

    def _prepare_provider_settings(self, provider_name: str, provider_config: Dict) -> Dict:
        """根据中转商配置生成统一的设置字典"""
        # 名称映射：支持简写名称到完整名称的映射
        name_mapping = {
            "yes": "yescode"
        }
        # 如果 provider_config 中有 model_provider，优先使用；否则使用名称映射或原始名称
        if "model_provider" in provider_config and provider_config["model_provider"]:
            actual_model_provider = provider_config["model_provider"]
        else:
            actual_model_provider = name_mapping.get(provider_name, provider_name)
        
        settings = {
            "model_provider": actual_model_provider,
            "model": provider_config.get("model", "gpt-5-codex"),
            "model_reasoning_effort": provider_config.get("model_reasoning_effort", "high"),
            "network_access": provider_config.get("network_access") or None,
            "disable_response_storage": provider_config.get("disable_response_storage"),
            "wire_api": provider_config.get("wire_api", "responses"),
            "requires_openai_auth": provider_config.get("requires_openai_auth"),
            "env_key": provider_config.get("env_key"),
            "projects": provider_config.get("projects"),
            "auth_keys": provider_config.get("auth_keys"),
        }

        # 针对特定服务商的默认设置（根据实际 model_provider 判断）
        if actual_model_provider == "duck" or provider_name == "duck":
            # duck 需要 network_access, disable_response_storage, requires_openai_auth
            settings["requires_openai_auth"] = True
            settings["disable_response_storage"] = True
            if not settings.get("network_access"):
                settings["network_access"] = "enabled"
            # duck 不需要 env_key
            if "env_key" in settings:
                del settings["env_key"]
            # duck 的 auth.json 只需要 OPENAI_API_KEY
            if not settings.get("auth_keys"):
                settings["auth_keys"] = {
                    "OPENAI_API_KEY": "api_key"
                }
        elif actual_model_provider == "yescode" or provider_name in ("yescode", "yes"):
            # yescode 不需要 requires_openai_auth, disable_response_storage, network_access
            settings["requires_openai_auth"] = None
            settings["disable_response_storage"] = None
            settings["network_access"] = None
            settings["env_key"] = "YESCODE_API_KEY"
            
            # yescode 强制使用正确的 base_url
            correct_base_url = "https://cotest.yes.vg/v1"
            provider_config["base_url"] = correct_base_url

            # yescode 官方配置示例中没有 projects 配置块，如果需要可以显式配置
            # 不自动添加 projects 配置，以匹配官方示例

            # auth.json 需要同时写入 OPENAI_API_KEY 与专属的 env_key
            # 如果配置中没有 auth_keys，则设置默认值
            if not settings.get("auth_keys"):
                env_key = settings["env_key"]
                settings["auth_keys"] = {
                    "OPENAI_API_KEY": "api_key",
                    env_key: "api_key"
                }
            # 如果配置中有 auth_keys，确保它包含必要的键
            elif settings.get("auth_keys"):
                auth_keys = settings["auth_keys"]
                env_key = settings["env_key"]
                # 确保 OPENAI_API_KEY 和 env_key 都存在
                if "OPENAI_API_KEY" not in auth_keys:
                    auth_keys["OPENAI_API_KEY"] = "api_key"
                if env_key not in auth_keys:
                    auth_keys[env_key] = "api_key"
        else:
            settings.setdefault("requires_openai_auth", True)
            settings.setdefault("disable_response_storage", True)

        if not settings.get("auth_keys"):
            # 默认仅写入 OPENAI_API_KEY
            settings["auth_keys"] = {
                "OPENAI_API_KEY": "api_key"
            }

        return settings

    def generate_config_toml(self, provider_name: str, provider_config: Dict) -> str:
        """
        生成 config.toml 内容

        Args:
            provider_name: 中转商名称
            provider_config: 中转商配置信息
        """
        settings = self._prepare_provider_settings(provider_name, provider_config)

        def format_toml_value(value):
            if isinstance(value, bool):
                return 'true' if value else 'false'
            elif isinstance(value, (int, float)):
                return str(value)
            return f'"{value}"'

        lines = [
            f'model_provider = "{settings["model_provider"]}"',
            f'model = "{settings["model"]}"'
        ]

        if settings.get("model_reasoning_effort"):
            lines.append(f'model_reasoning_effort = "{settings["model_reasoning_effort"]}"')

        # 添加可选配置（仅当值不为 None 时写入）
        if settings.get("network_access") is not None:
            lines.append(f'network_access = "{settings["network_access"]}"')

        disable_storage = settings.get("disable_response_storage")
        if disable_storage is True:
            lines.append('disable_response_storage = true')
        elif disable_storage is False:
            lines.append('disable_response_storage = false')

        lines.append("")  # 空行分隔

        # 添加 model_providers 配置块（使用 settings 中的 model_provider，而不是 provider_name）
        model_provider = settings["model_provider"]
        lines.append(f'[model_providers.{model_provider}]')
        lines.append(f'name = "{model_provider}"')
        lines.append(f'base_url = "{provider_config["base_url"]}"')

        if settings.get("wire_api"):
            lines.append(f'wire_api = "{settings["wire_api"]}"')

        # 仅在 env_key 存在且不为 None 时写入
        if settings.get("env_key") is not None:
            lines.append(f'env_key = "{settings["env_key"]}"')

        # 仅在 requires_openai_auth 为 True 时写入（yescode 不需要此字段）
        if settings.get("requires_openai_auth") is True:
            lines.append('requires_openai_auth = true')
        elif settings.get("requires_openai_auth") is False and provider_config.get("requires_openai_auth") is not None:
            # 仅当用户显式配置为 false 时才输出，避免破坏官方示例
            lines.append('requires_openai_auth = false')

        # 添加 projects 配置块
        projects = settings.get("projects") or {}
        for project_path, project_conf in projects.items():
            lines.append("")
            lines.append(f'[projects."{project_path}"]')
            for key, value in project_conf.items():
                lines.append(f'{key} = {format_toml_value(value)}')

        return "\n".join(lines) + "\n"

    def update_auth_json(self, provider_name: str, provider_config: Dict, api_key: str):
        """更新 auth.json 文件"""
        settings = self._prepare_provider_settings(provider_name, provider_config)
        auth_data = {}

        for key_name, source in settings["auth_keys"].items():
            if source == "api_key" or source == "OPENAI_API_KEY":
                auth_data[key_name] = api_key
            else:
                # 允许从 provider_config 中读取其他字段
                auth_data[key_name] = provider_config.get(source, "")

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
            self.update_auth_json(provider_name, provider_config, api_key)
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
