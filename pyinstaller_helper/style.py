"""ttk 样式配置（clam 主题支持自定义颜色）"""

from tkinter import ttk

from . import config


def apply_style(root):
    """应用全局 ttk 样式，须在构建任何 ttk 部件前调用"""
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=config.BG, foreground=config.FG, font=(config.FONT, 9))
    style.configure("TLabel", background=config.BG)
    style.configure("Card.TLabel", background=config.CARD_BG, foreground=config.FG)
    style.configure(
        "Hint.TLabel", background=config.CARD_BG, foreground=config.FG_HINT, font=(config.FONT, 8)
    )
    style.configure("Card.TFrame", background=config.CARD_BG)
    style.configure("Card.TLabelframe", background=config.CARD_BG, borderwidth=1)
    style.configure(
        "Card.TLabelframe.Label",
        background=config.CARD_BG,
        foreground=config.CARD_LABEL_FG,
        font=(config.FONT, 9, "bold"),
    )
    style.configure("TCheckbutton", background=config.CARD_BG)
    style.configure("TEntry", fieldbackground=config.CARD_BG, padding=4)
    style.configure("TCombobox", fieldbackground=config.CARD_BG, padding=4)
    style.configure("TButton", padding=(14, 5))
    style.configure(
        "Accent.TButton",
        background=config.ACCENT,
        foreground="#ffffff",
        font=(config.FONT, 10, "bold"),
        padding=(24, 7),
    )
    style.map(
        "Accent.TButton",
        background=[("active", config.ACCENT_DARK), ("disabled", config.ACCENT_DISABLED_BG)],
        foreground=[("disabled", config.ACCENT_DISABLED_FG)],
    )
