"""打包选项卡片：复选框与调试等级下拉框（仅界面构建，不含弹窗）"""

import tkinter as tk
from tkinter import ttk


class OptionsCard(ttk.LabelFrame):
    """打包选项卡片，自带复选框变量与调试等级下拉框"""

    def __init__(self, parent):
        super().__init__(parent, text=" 打包选项 ", style="Card.TLabelframe")
        self.onefile_var = tk.BooleanVar()
        self.windowed_var = tk.BooleanVar()
        self.noconfirm_var = tk.BooleanVar()
        self.clean_var = tk.BooleanVar()
        self.debug_var = tk.BooleanVar()
        self.debug_level = tk.StringVar()
        self._vars = {
            "onefile": self.onefile_var,
            "windowed": self.windowed_var,
            "noconfirm": self.noconfirm_var,
            "clean": self.clean_var,
            "debug": self.debug_var,
            "debug_level": self.debug_level,
        }
        self.pack(fill="x", pady=(0, 10))
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        pairs = [
            (self.onefile_var, "单文件模式 (--onefile)"),
            (self.windowed_var, "隐藏控制台窗口 (--windowed)"),
            (self.noconfirm_var, "覆盖输出不询问 (--noconfirm)"),
            (self.clean_var, "清理构建文件 (--clean)"),
        ]
        for i, (var, text) in enumerate(pairs):
            ttk.Checkbutton(self, text=text, variable=var).grid(
                row=i // 2, column=i % 2, sticky="w", padx=12, pady=4
            )

        # 调试模式 + 等级下拉框
        ttk.Checkbutton(self, text="调试模式 (--debug)", variable=self.debug_var).grid(
            row=2, column=0, sticky="w", padx=12, pady=4
        )
        level_box = ttk.Frame(self, style="Card.TFrame")
        level_box.grid(row=2, column=1, sticky="w", padx=12, pady=4)
        ttk.Label(level_box, text="等级:", style="Card.TLabel").pack(
            side="left", padx=(0, 6)
        )
        self.debug_level_combo = ttk.Combobox(
            level_box,
            textvariable=self.debug_level,
            width=14,
            state="readonly",
            values=["all", "imports", "bootloader", "noarchive"],
        )
        self.debug_level_combo.pack(side="left")

    def toggle_debug_level(self, *_):
        """调试等级下拉框跟随"调试模式"勾选启用/禁用"""
        self.debug_level_combo.config(
            state="readonly" if self.debug_var.get() else "disabled"
        )

    def values(self):
        """导出本卡片表单内容（键名与 settings 模块一致）"""
        return {key: var.get() for key, var in self._vars.items()}

    def apply_values(self, values):
        """回填表单内容，未出现的键保持原值"""
        for key, var in self._vars.items():
            if key in values:
                var.set(values[key])
