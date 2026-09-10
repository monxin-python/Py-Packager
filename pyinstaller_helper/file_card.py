"""文件设置卡片：脚本/图标/输出等路径与文本输入 + 结果预览（仅界面构建，不含弹窗）"""

import base64
import os
import tkinter as tk
from tkinter import ttk

from . import config
from .icon import icon_to_png, image_to_png

PREVIEW_SIZE = 48  # 预览图标的边长（像素）
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp"}  # 走 GDI+ 预览的普通图片格式


class FileCard(ttk.LabelFrame):
    """文件设置卡片，自带各输入框变量与右侧结果预览（最终 exe 的图标 + 名称）"""

    def __init__(self, parent, on_select_script, on_select_icon, on_select_output):
        super().__init__(parent, text=" 文件设置 ", style="Card.TLabelframe")
        self.script_path = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.data_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.hidden_var = tk.StringVar()
        self._vars = {
            "script": self.script_path,
            "icon": self.icon_path,
            "output": self.output_path,
            "data": self.data_var,
            "name": self.name_var,
            "hidden": self.hidden_var,
        }
        self.pack(fill="x", pady=(0, 10))
        self.columnconfigure(1, weight=1)
        self._build_preview()

        rows = [
            ("Python 文件", self.script_path, "选择", on_select_script, None),
            ("图标 (ico/图片)", self.icon_path, "选择", on_select_icon, None),
            ("输出路径", self.output_path, "选择", on_select_output, None),
            ("额外数据文件", self.data_var, None, None, "格式：源路径;目标路径"),
            ("程序名称", self.name_var, None, None, "--name · 留空则用脚本名"),
            ("隐藏导入模块", self.hidden_var, None, None, "--hidden-import · 逗号分隔"),
        ]
        for i, (label, var, btn_text, btn_cmd, hint) in enumerate(rows):
            ttk.Label(self, text=label, style="Card.TLabel").grid(
                row=i, column=0, sticky="e", padx=(12, 8), pady=6
            )
            ttk.Entry(self, textvariable=var).grid(
                row=i, column=1, sticky="ew", padx=(0, 8)
            )
            if btn_text:
                ttk.Button(self, text=btn_text, command=btn_cmd).grid(
                    row=i, column=2, padx=(0, 8)
                )
            if hint:
                ttk.Label(self, text=hint, style="Hint.TLabel").grid(
                    row=i, column=3, sticky="w", padx=(0, 12)
                )

        # 表单变化时实时刷新预览
        self.icon_path.trace_add("write", self._refresh_icon)
        self.script_path.trace_add("write", self._refresh_name)
        self.name_var.trace_add("write", self._refresh_name)
        self._refresh_icon()
        self._refresh_name()

    # ---------------------------------------------------------------- 结果预览
    def _build_preview(self):
        """结果预览：排在三个「选择」按钮后面（前 3 行、第 3 列，垂直居中）"""
        box = ttk.Frame(self, style="Card.TFrame")
        box.grid(row=0, column=3, rowspan=3, sticky="w", padx=(10, 0))
        self._placeholder = tk.PhotoImage(width=PREVIEW_SIZE, height=PREVIEW_SIZE)
        self._placeholder.put(
            config.CARD_BG, to=(0, 0, PREVIEW_SIZE, PREVIEW_SIZE)
        )
        self._icon_photo = None  # 持有引用，防止 PhotoImage 被 GC 回收
        self._icon_label = tk.Label(
            box,
            image=self._placeholder,
            bg=config.CARD_BG,
            highlightthickness=1,
            highlightbackground=config.BORDER,
        )
        self._icon_label.pack()
        self._name_label = ttk.Label(
            box,
            text="",
            style="Hint.TLabel",
            anchor="center",
            justify="center",
            wraplength=92,
        )
        self._name_label.pack(pady=(4, 0))

    def _refresh_icon(self, *_args):
        """根据图标路径更新缩略图；提取失败退回占位图"""
        path = self.icon_path.get().strip()
        photo = None
        if path and os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext == ".ico":
                png = icon_to_png(path, PREVIEW_SIZE)
            elif ext in IMAGE_EXTS:
                png = image_to_png(path, PREVIEW_SIZE)
            else:
                png = None
            if png:
                photo = tk.PhotoImage(data=base64.b64encode(png))
        self._icon_photo = photo
        self._icon_label.configure(image=photo or self._placeholder)

    def _refresh_name(self, *_args):
        """预览最终 exe 名称：程序名称留空时用脚本文件名（与 --name 行为一致）"""
        name = self.name_var.get().strip()
        if not name:
            script = self.script_path.get().strip()
            name = os.path.splitext(os.path.basename(script))[0] if script else ""
        self._name_label.configure(text=f"{name}.exe" if name else "")

    def values(self):
        """导出本卡片表单内容（键名与 settings 模块一致）"""
        return {key: var.get() for key, var in self._vars.items()}

    def apply_values(self, values):
        """回填表单内容，未出现的键保持原值"""
        for key, var in self._vars.items():
            if key in values:
                var.set(values[key])
