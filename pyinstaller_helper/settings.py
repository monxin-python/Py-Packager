"""设置持久化：读写 pyinstaller_settings.json（纯逻辑，不依赖 GUI）"""

import json
import os

from . import config

# 各表单字段的默认值（首次启动 / 恢复默认时使用）
DEFAULT_SETTINGS = {
    # 路径与文本
    "script": "",
    "icon": "",
    "output": "",
    "data": "",
    "name": "",
    "hidden": "",
    # 打包选项
    "onefile": True,
    "windowed": False,
    "noconfirm": True,  # 避免重复打包时询问覆盖
    "clean": False,
    "debug": False,
    "debug_level": "all",
}


def load_settings():
    """读取保存的设置并与默认值合并；文件不存在、损坏或类型不符时用默认值"""
    try:
        with open(config.SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if not isinstance(saved, dict):
            saved = {}
    except (OSError, ValueError):
        saved = {}
    merged = dict(DEFAULT_SETTINGS)
    for key, default in DEFAULT_SETTINGS.items():
        if isinstance(saved.get(key), type(default)):
            merged[key] = saved[key]
    return merged


def save_settings(settings):
    """把设置字典写入文件；失败静默降级，不影响主流程"""
    try:
        os.makedirs(os.path.dirname(config.SETTINGS_FILE), exist_ok=True)
        with open(config.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def clear_settings_file():
    """删除设置文件（表单重置由 GUI 层负责）"""
    try:
        os.remove(config.SETTINGS_FILE)
    except OSError:
        pass
