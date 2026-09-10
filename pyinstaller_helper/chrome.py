"""窗口外壳部件：顶部标题栏、底部状态栏、操作按钮（仅界面构建，不含弹窗）"""

import tkinter as tk
from tkinter import ttk

from . import config


class Header(tk.Frame):
    """顶部标题区"""

    def __init__(self, parent):
        super().__init__(parent, bg=config.BG)
        self.pack(fill="x", padx=16, pady=(14, 10))
        tk.Label(
            self,
            text="PyInstaller 快捷打包工具",
            bg=config.BG,
            fg=config.TITLE_FG,
            font=(config.FONT, 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            self,
            text="图形化配置打包参数 · 实时查看打包日志",
            bg=config.BG,
            fg=config.FG_GRAY,
            font=(config.FONT, 9),
        ).pack(anchor="w", pady=(2, 0))


class StatusBar(tk.Label):
    """状态栏（先 pack，固定在底部）"""

    def __init__(self, parent, status_var):
        super().__init__(
            parent,
            textvariable=status_var,
            anchor="w",
            bg=config.STATUS_BG,
            fg=config.STATUS_FG,
            font=(config.FONT, 9),
            padx=12,
            pady=3,
        )
        self.pack(fill="x", side="bottom")


class ActionsBar(ttk.Frame):
    """操作按钮区：开始打包 / 打开输出文件夹 / 复制命令"""

    def __init__(self, parent, on_build, on_open_output, on_copy):
        super().__init__(parent)
        self.pack(fill="x", pady=(0, 10))
        self.build_button = ttk.Button(
            self, text="开始打包", style="Accent.TButton", command=on_build
        )
        self.build_button.pack(side="left")
        ttk.Button(self, text="打开输出文件夹", command=on_open_output).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(self, text="复制命令", command=on_copy).pack(side="left", padx=(8, 0))
