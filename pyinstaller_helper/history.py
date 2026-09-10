"""最近文件历史记录：读写 pyinstaller_history.json（纯逻辑，不依赖 GUI）"""

import json
import os

from . import config


def load_history():
    """读取历史记录，文件不存在或损坏时静默降级为空列表"""
    try:
        with open(config.HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        if isinstance(history, list):
            return [p for p in history if isinstance(p, str)]
    except (OSError, ValueError):
        pass
    return []


def save_history(path):
    """保存历史记录；已存在的路径移到最前"""
    history = load_history()
    if path in history:
        history.remove(path)
    history.insert(0, path)
    try:
        os.makedirs(os.path.dirname(config.HISTORY_FILE), exist_ok=True)
        with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[: config.HISTORY_LIMIT], f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # 写历史失败不影响打包主流程


def clear_history_file():
    """删除历史记录文件（菜单刷新由 GUI 层负责）"""
    try:
        os.remove(config.HISTORY_FILE)
    except OSError:
        pass


def short_path(path, limit=60):
    """菜单中过长的路径从中间截断"""
    if len(path) <= limit:
        return path
    half = limit // 2
    return path[: half - 2] + "..." + path[-(half - 1) :]
