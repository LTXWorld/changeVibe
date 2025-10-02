import json
import os
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """管理 Claude Switcher 配置文件"""

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "claude-switcher"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """确保配置目录和文件存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if not self.config_file.exists():
            # 创建默认配置
            default_config = {
                "providers": {
                    "fox": {
                        "token": "",
                        "base_url": "https://code.newcli.com/claude"
                    },
                    "duck": {
                        "token": "",
                        "base_url": "https://jp.instcopilot-api.com"
                    },
                    "88code": {
                        "token": "",
                        "base_url": "https://www.88code.org/api"
                    },
                    "packy": {
                        "token": "",
                        "base_url": "https://api.packycode.com"
                    }
                },
                "codex_providers": {
                    "fox": {
                        "api_key": "",
                        "base_url": "https://code.newcli.com/codex/v1",
                        "network_access": ""
                    },
                    "duck": {
                        "api_key": "",
                        "base_url": "https://jp.duckcoding.com/v1",
                        "network_access": "enabled"
                    }
                },
                "current": None,
                "current_codex": None,
                "env_vars": {
                    "token": "ANTHROPIC_AUTH_TOKEN",
                    "base_url": "ANTHROPIC_BASE_URL"
                }
            }
            self._save_config(default_config)
            # 设置文件权限为 600（仅所有者可读写）
            os.chmod(self.config_file, 0o600)

    def _load_config(self) -> Dict:
        """加载配置文件"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_config(self, config: Dict):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get_providers(self) -> Dict:
        """获取所有中转商配置"""
        config = self._load_config()
        return config.get("providers", {})

    def get_provider(self, name: str) -> Optional[Dict]:
        """获取指定中转商配置"""
        providers = self.get_providers()
        return providers.get(name)

    def add_provider(self, name: str, token: str, base_url: str):
        """添加新的中转商"""
        config = self._load_config()
        config["providers"][name] = {
            "token": token,
            "base_url": base_url
        }
        self._save_config(config)

    def remove_provider(self, name: str) -> bool:
        """删除中转商"""
        config = self._load_config()
        if name in config["providers"]:
            del config["providers"][name]
            # 如果删除的是当前激活的，清空 current
            if config.get("current") == name:
                config["current"] = None
            self._save_config(config)
            return True
        return False

    def set_current(self, name: str) -> bool:
        """设置当前激活的中转商"""
        config = self._load_config()
        if name in config["providers"]:
            config["current"] = name
            self._save_config(config)
            return True
        return False

    def get_current(self) -> Optional[str]:
        """获取当前激活的中转商名称"""
        config = self._load_config()
        return config.get("current")

    def get_current_provider(self) -> Optional[Dict]:
        """获取当前激活的中转商配置"""
        current = self.get_current()
        if current:
            return self.get_provider(current)
        return None

    def get_env_vars(self) -> Dict[str, str]:
        """获取环境变量名称配置"""
        config = self._load_config()
        return config.get("env_vars", {})

    # Codex 相关方法
    def get_codex_providers(self) -> Dict:
        """获取所有 Codex 中转商配置"""
        config = self._load_config()
        return config.get("codex_providers", {})

    def get_codex_provider(self, name: str) -> Optional[Dict]:
        """获取指定 Codex 中转商配置"""
        providers = self.get_codex_providers()
        return providers.get(name)

    def add_codex_provider(self, name: str, api_key: str, base_url: str, network_access: str = ""):
        """添加新的 Codex 中转商"""
        config = self._load_config()
        if "codex_providers" not in config:
            config["codex_providers"] = {}

        config["codex_providers"][name] = {
            "api_key": api_key,
            "base_url": base_url,
            "network_access": network_access
        }
        self._save_config(config)

    def remove_codex_provider(self, name: str) -> bool:
        """删除 Codex 中转商"""
        config = self._load_config()
        if "codex_providers" in config and name in config["codex_providers"]:
            del config["codex_providers"][name]
            # 如果删除的是当前激活的，清空 current_codex
            if config.get("current_codex") == name:
                config["current_codex"] = None
            self._save_config(config)
            return True
        return False

    def set_current_codex(self, name: str) -> bool:
        """设置当前激活的 Codex 中转商"""
        config = self._load_config()
        if "codex_providers" in config and name in config["codex_providers"]:
            config["current_codex"] = name
            self._save_config(config)
            return True
        return False

    def get_current_codex(self) -> Optional[str]:
        """获取当前激活的 Codex 中转商名称"""
        config = self._load_config()
        return config.get("current_codex")

    def get_current_codex_provider(self) -> Optional[Dict]:
        """获取当前激活的 Codex 中转商配置"""
        current = self.get_current_codex()
        if current:
            return self.get_codex_provider(current)
        return None

