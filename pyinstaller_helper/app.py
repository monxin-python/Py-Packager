"""GUI 主窗口：组装各界面部件，承载业务逻辑与弹窗交互"""

import os
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import config, settings
from .analyzer import check_input_functions
from .build_process import BuildProcess
from .chrome import ActionsBar, Header, StatusBar
from .command import BuildConfig, assemble_command, find_pyinstaller, format_cmd, validate_inputs
from .file_card import FileCard
from .history import clear_history_file, load_history, save_history
from .icon import image_to_ico
from .menubar import MenuBar
from .options_card import OptionsCard
from .panels import LogPanel, PreviewPanel
from .style import apply_style


class App:
    """PyInstaller 快捷打包工具主窗口（控制器：组装部件、编排业务）"""

    def __init__(self):
        self.build_proc = BuildProcess()
        self._init_root()
        self._build_ui()
        self._apply_settings(settings.load_settings())
        self._bind_events()
        self.update_history_menu()
        self.poll_log()

    def run(self):
        self.root.mainloop()

    # ---------------------------------------------------------------- 初始化
    def _init_root(self):
        self.root = tk.Tk()
        self.root.title("PyInstaller 快捷打包工具_v3  by：Hu_Tiger")
        self.root.geometry("860x750")
        self.root.minsize(760, 650)
        self.root.configure(bg=config.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        apply_style(self.root)
        self.status_var = tk.StringVar(value="就绪")

    # ---------------------------------------------------------------- 界面组装
    def _build_ui(self):
        StatusBar(self.root, self.status_var)
        Header(self.root)
        content = ttk.Frame(self.root)
        content.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.file_card = FileCard(
            content,
            on_select_script=self.select_script,
            on_select_icon=self.select_icon,
            on_select_output=self.select_output,
        )
        self.options_card = OptionsCard(content)
        self.preview = PreviewPanel(content)
        self.actions = ActionsBar(
            content,
            on_build=self.run_pyinstaller,
            on_open_output=self.open_output_dir,
            on_copy=self.copy_command,
        )
        self.log = LogPanel(content)
        self.menubar = MenuBar(
            self.root,
            on_save_settings=self.save_current_settings,
            on_reset_settings=self.reset_settings,
            on_clear_history=self.clear_history,
        )

    def _bind_events(self):
        self.options_card.debug_var.trace_add(
            "write", self.options_card.toggle_debug_level
        )
        self.options_card.toggle_debug_level()
        self.root.bind("<Control-s>", lambda _e: self.save_current_settings())

    # ---------------------------------------------------------------- 文件选择
    def select_script(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            self.file_card.script_path.set(path)
            save_history(path)
            self.update_history_menu()
            self.status_var.set(f"已选择脚本：{os.path.basename(path)}")

    def select_icon(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("图标/图片文件", "*.ico *.png *.jpg *.jpeg *.bmp"),
                ("Icon Files", "*.ico"),
                ("图片文件", "*.png *.jpg *.jpeg *.bmp"),
            ]
        )
        if not path:
            return
        if os.path.splitext(path)[1].lower() != ".ico":
            path = self._convert_image_to_ico(path)
            if not path:
                return
        self.file_card.icon_path.set(path)

    def _convert_image_to_ico(self, image_path):
        """图片自动转 ICO：写到源文件同目录同名 .ico；失败或取消返回 None"""
        ico_path = os.path.splitext(image_path)[0] + ".ico"
        if os.path.isfile(ico_path) and not messagebox.askyesno(
            "覆盖确认", f"已存在同名图标文件：\n{ico_path}\n\n是否覆盖？"
        ):
            return None
        data = image_to_ico(image_path)
        if not data:
            messagebox.showerror("转换失败", f"无法把该图片转换为 ICO：\n{image_path}")
            return None
        with open(ico_path, "wb") as f:
            f.write(data)
        self.status_var.set(f"已转换图标：{os.path.basename(ico_path)}")
        return ico_path

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.file_card.output_path.set(path)

    # ---------------------------------------------------------------- 历史菜单
    def update_history_menu(self):
        self.menubar.set_history(load_history(), on_pick=self._pick_history)

    def _pick_history(self, path):
        self.file_card.script_path.set(path)

    def clear_history(self):
        clear_history_file()
        self.update_history_menu()

    # ---------------------------------------------------------------- 设置保存/恢复
    def _collect_settings(self):
        """把两个表单卡片的内容合并为设置字典"""
        return {**self.file_card.values(), **self.options_card.values()}

    def _apply_settings(self, saved):
        """把设置字典回填到表单（saved 已与默认值合并）"""
        self.file_card.apply_values(saved)
        self.options_card.apply_values(saved)

    def save_current_settings(self):
        """保存当前表单内容（Ctrl+S / 菜单 / 关闭窗口时调用）"""
        settings.save_settings(self._collect_settings())
        self.status_var.set("设置已保存")

    def reset_settings(self):
        """恢复默认设置（需确认；删除设置文件并重置表单）"""
        if not messagebox.askyesno("恢复默认", "确定要恢复默认设置吗？"):
            return
        settings.clear_settings_file()
        self._apply_settings(settings.DEFAULT_SETTINGS)
        self.preview.clear()
        self.status_var.set("已恢复默认设置")

    # ---------------------------------------------------------------- 命令构建
    def _collect_config(self):
        """把表单内容收集为 BuildConfig"""
        return BuildConfig(**self._collect_settings())

    def build_command(self):
        """校验参数并生成命令列表（含弹窗交互）；失败返回 None"""
        cfg = self._collect_config()
        err = validate_inputs(cfg)
        if err:
            messagebox.showerror("错误", err)
            return None

        # 自动检测 input()/getpass()：--windowed 与其冲突，会导致打包后运行报错
        if cfg.windowed and check_input_functions(cfg.script):
            answer = messagebox.askyesno(
                "警告",
                "检测到脚本中使用了 input() 或 getpass()，\n"
                "隐藏控制台 (--windowed) 会导致运行报错。\n"
                "是否自动取消隐藏控制台选项？",
            )
            if answer:
                self.options_card.windowed_var.set(False)
                cfg.windowed = False

        base = find_pyinstaller()
        if base is None:
            messagebox.showerror(
                "错误",
                "未找到 PyInstaller，请先执行：\n\n    pip install pyinstaller",
            )
            return None

        cmd = assemble_command(base, cfg)
        self._show_preview(cmd)
        return cmd

    def _show_preview(self, cmd):
        self.preview.show(format_cmd(cmd))

    def get_output_dir(self):
        if self.file_card.output_path.get():
            return self.file_card.output_path.get()
        return os.path.abspath("dist")

    def open_output_dir(self):
        out_dir = self.get_output_dir()
        if os.path.isdir(out_dir):
            os.startfile(out_dir)  # Windows 专用
        else:
            messagebox.showwarning("提示", f"输出目录不存在：{out_dir}")

    def copy_command(self):
        text = self.preview.get_text()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log.append("[已复制命令到剪贴板]\n")

    # ---------------------------------------------------------------- 打包执行
    def run_pyinstaller(self):
        if self.build_proc.is_running():
            messagebox.showwarning("提示", "打包正在进行中，请稍候")
            return
        cmd = self.build_command()
        if not cmd:
            return
        self.actions.build_button.config(state=tk.DISABLED, text="打包中...")
        self.status_var.set("正在打包，请稍候...")
        self.log.clear()
        self.log.append("$ " + format_cmd(cmd) + "\n\n")
        self.build_proc.start(cmd)

    def poll_log(self):
        """主线程定时取出队列内容，更新日志界面"""
        try:
            while True:
                kind, msg = self.build_proc.queue.get_nowait()
                if kind == "OUT":
                    self.log.append(msg)
                elif kind == "ERROR":
                    self.actions.build_button.config(state=tk.NORMAL, text="开始打包")
                    self.status_var.set("启动 PyInstaller 失败")
                    self.log.append(f"\n[错误] {msg}\n")
                    messagebox.showerror("错误", f"启动 PyInstaller 失败：\n{msg}")
                elif kind == "DONE":
                    self.actions.build_button.config(state=tk.NORMAL, text="开始打包")
                    if msg == 0:
                        self.status_var.set("打包完成")
                        self.log.append("\n[打包完成]\n")
                        out_dir = self.get_output_dir()
                        if messagebox.askyesno(
                            "成功",
                            f"打包完成！\n输出目录：{out_dir}\n\n是否立即打开输出文件夹？",
                        ):
                            self.open_output_dir()
                    else:
                        self.status_var.set(f"打包失败（退出码 {msg}）")
                        self.log.append(f"\n[打包失败] 退出码：{msg}\n")
                        messagebox.showerror(
                            "失败", f"打包失败（退出码 {msg}），请查看下方日志"
                        )
        except queue.Empty:
            pass
        self.log.see_end()
        self.root.after(100, self.poll_log)

    def on_close(self):
        """关闭窗口时先保存设置；若打包仍在进行则询问是否终止"""
        if self.build_proc.is_running():
            if not messagebox.askyesno("退出", "打包仍在进行，确定要终止并退出吗？"):
                return
            self.build_proc.terminate()
        self.save_current_settings()
        self.root.destroy()


if __name__ == "__main__":
    App().run()
