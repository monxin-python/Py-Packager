"""打包历史记录：读写 pyinstaller_history.json（纯逻辑，不依赖 GUI）

每条记录是一份完整的表单快照（键名与 settings.DEFAULT_SETTINGS 一致），
只有打包成功时才写入；旧版的纯路径数组读取时自动兼容。
"""

import json
import os

from . import config


def load_history():
    """读取历史记录，文件不存在、损坏或条目无法识别时静默降级为空列表"""
    try:
        with open(config.HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        if isinstance(history, list):
            return [e for e in (_as_entry(x) for x in history) if e]
    except (OSError, ValueError):
        pass
    return []


def _as_entry(item):
    """把一条记录统一成字典；纯路径（旧格式）视为只记录了脚本"""
    if isinstance(item, str):
        return {"script": item}
    if isinstance(item, dict) and isinstance(item.get("script"), str):
        return item
    return None


def save_history(cfg):
    """记录一次打包：整份配置快照写到最前，同一脚本的旧记录先删掉"""
    script = cfg.get("script", "")
    if not script:
        return
    history = [e for e in load_history() if e.get("script") != script]
    history.insert(0, dict(cfg))
    try:
        os.makedirs(os.path.dirname(config.HISTORY_FILE), exist_ok=True)
        with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(
                history[: config.HISTORY_LIMIT], f, ensure_ascii=False, indent=2
            )
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


if __name__ == "__main__":
    # 自检：旧格式兼容、同脚本去重且置顶、坏条目跳过
    import tempfile

    _fd, _tmp = tempfile.mkstemp(suffix=".json")
    os.close(_fd)
    _real = config.HISTORY_FILE
    config.HISTORY_FILE = _tmp
    try:
        with open(_tmp, "w", encoding="utf-8") as f:  # 旧格式：纯路径数组
            json.dump(["H:/a.py", "H:/b.py"], f)
        assert load_history() == [{"script": "H:/a.py"}, {"script": "H:/b.py"}]

        save_history({"script": "H:/b.py", "name": "b", "onefile": False})
        _h = load_history()
        assert _h[0] == {"script": "H:/b.py", "name": "b", "onefile": False}, _h
        assert len(_h) == 2, _h  # b 被置顶而不是新增一条

        with open(_tmp, "w", encoding="utf-8") as f:  # 坏条目混入
            json.dump(["H:/a.py", 42, {"no_script": 1}], f)
        assert load_history() == [{"script": "H:/a.py"}]

        save_history({"script": ""})  # 空脚本不写
        assert load_history() == [{"script": "H:/a.py"}]
    finally:
        config.HISTORY_FILE = _real
        os.remove(_tmp)
    print("自检通过")
