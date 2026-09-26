"""菜单栏：最近打包记录与设置菜单（仅界面构建，不含弹窗）"""

import tkinter as tk

from .history import short_path


class MenuBar:
    """窗口菜单栏，负责菜单创建与最近打包记录刷新"""

    def __init__(self, root, on_save_settings, on_reset_settings, on_clear_history):
        menubar = tk.Menu(root)
        self.history_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="最近打包", menu=self.history_menu)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(
            label="保存当前设置", accelerator="Ctrl+S", command=on_save_settings
        )
        settings_menu.add_command(label="恢复默认设置", command=on_reset_settings)
        menubar.add_cascade(label="设置", menu=settings_menu)
        self._on_clear_history = on_clear_history
        root.config(menu=menubar)

    def set_history(self, entries, on_pick):
        """刷新最近打包列表；entries 是配置快照，标签取其中的脚本路径"""
        self.history_menu.delete(0, tk.END)
        if not entries:
            self.history_menu.add_command(label="（暂无记录）", state=tk.DISABLED)
        else:
            for entry in entries:
                self.history_menu.add_command(
                    label=short_path(entry.get("script", "")),
                    command=lambda x=entry: on_pick(x),
                )
        self.history_menu.add_separator()
        self.history_menu.add_command(label="清除历史", command=self._on_clear_history)
