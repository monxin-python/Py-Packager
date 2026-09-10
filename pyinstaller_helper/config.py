"""全局配置：历史/设置文件路径与界面配色"""

import os
import sys


def _data_dir():
    """数据文件目录：打包后放在 %LOCALAPPDATA%，源码运行时放在项目根目录

    打包成 exe 后 __file__ 指向临时解压目录（onefile）或程序目录（onedir），
    都不适合持久化用户数据；frozen 时改用当前用户的 LOCALAPPDATA。
    """
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "PyInstallerHelper")
    # 源码运行时固定在项目根目录（包的上一级），避免因启动目录不同而"丢失"历史
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


HISTORY_FILE = os.path.join(_data_dir(), "pyinstaller_history.json")
HISTORY_LIMIT = 10

# 设置文件与历史文件同目录
SETTINGS_FILE = os.path.join(_data_dir(), "pyinstaller_settings.json")

# 通用配色与字体
BG = "#f4f6f9"          # 窗口背景
CARD_BG = "#ffffff"     # 卡片背景
FG = "#1f2937"          # 正文颜色
FG_GRAY = "#6b7280"     # 次要文字
FG_HINT = "#9ca3af"     # 提示文字
BORDER = "#e2e8f0"      # 边框
ACCENT = "#2ea44f"      # 主按钮绿色
ACCENT_DARK = "#238636"
FONT = "Microsoft YaHei UI"
MONO = "Consolas"

# 各区块专用颜色
TITLE_FG = "#111827"          # 顶部标题
CARD_LABEL_FG = "#374151"     # 卡片标题
PREVIEW_BG = "#fafbfc"        # 命令预览背景
PREVIEW_FG = "#374151"
STATUS_BG = "#eceff3"         # 状态栏背景
STATUS_FG = "#4b5563"         # 状态栏文字
LOG_BG = "#1e1e1e"            # 日志背景（深色控制台风格）
LOG_FG = "#d4d4d4"            # 日志文字
LOG_CURSOR = "#ffffff"
LOG_SELECT = "#264f78"
ACCENT_DISABLED_BG = "#b5bcc4"
ACCENT_DISABLED_FG = "#f3f4f6"
