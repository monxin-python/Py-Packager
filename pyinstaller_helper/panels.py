"""输出面板：命令预览与打包日志（深色控制台风格，仅界面构建，不含弹窗）"""

import tkinter as tk
from tkinter import scrolledtext, ttk

from . import config


class PreviewPanel(ttk.LabelFrame):
    """命令预览面板（只读文本框）"""

    def __init__(self, parent):
        super().__init__(parent, text=" 命令预览 ", style="Card.TLabelframe")
        self.text = scrolledtext.ScrolledText(
            self,
            height=4,
            state=tk.DISABLED,
            wrap="word",
            font=(config.MONO, 9),
            bg=config.PREVIEW_BG,
            fg=config.PREVIEW_FG,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=config.BORDER,
            padx=8,
            pady=6,
        )
        self.text.pack(fill="x", padx=12, pady=(4, 12))
        self.pack(fill="x", pady=(0, 10))

    def show(self, text):
        """替换为指定文本"""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, text)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)

    def get_text(self):
        return self.text.get(1.0, tk.END).strip()


class LogPanel(ttk.LabelFrame):
    """打包日志面板（只读文本框，只允许追加/清空）"""

    def __init__(self, parent):
        super().__init__(parent, text=" 打包日志 ", style="Card.TLabelframe")
        self.text = scrolledtext.ScrolledText(
            self,
            height=10,
            state=tk.DISABLED,
            wrap="word",
            font=(config.MONO, 9),
            bg=config.LOG_BG,
            fg=config.LOG_FG,
            insertbackground=config.LOG_CURSOR,
            selectbackground=config.LOG_SELECT,
            relief=tk.FLAT,
            padx=8,
            pady=6,
        )
        self.text.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.pack(fill="both", expand=True)

    def append(self, msg):
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, msg)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)

    def see_end(self):
        self.text.see(tk.END)
