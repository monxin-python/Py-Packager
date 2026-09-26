"""打包命令构建：参数校验与 PyInstaller 命令生成（纯逻辑，不含弹窗）"""

import importlib.util
import os
import re
import shutil
import sys
from dataclasses import dataclass


@dataclass
class BuildConfig:
    """一次打包所需的全部参数（与 GUI 表单一一对应）"""

    script: str = ""
    icon: str = ""
    output: str = ""
    data: str = ""
    name: str = ""
    hidden: str = ""
    onefile: bool = True
    windowed: bool = False
    noconfirm: bool = True
    clean: bool = False
    debug: bool = False
    debug_level: str = "all"


def find_pyinstaller():
    """优先使用 PATH 中的 pyinstaller，否则回退到当前解释器的 PyInstaller 模块"""
    if shutil.which("pyinstaller"):
        return ["pyinstaller"]
    if importlib.util.find_spec("PyInstaller") is not None:
        return [sys.executable, "-m", "PyInstaller"]
    return None


def validate_inputs(cfg: BuildConfig):
    """打包前的参数校验，返回错误信息；None 表示通过"""
    if not cfg.script:
        return "请选择要打包的 Python 文件"
    if not os.path.isfile(cfg.script):
        return f"文件不存在：{cfg.script}"
    if cfg.icon and not os.path.isfile(cfg.icon):
        return f"图标文件不存在：{cfg.icon}"
    name = cfg.name.strip()
    if name and re.search(r'[\\/:*?"<>|]', name):
        return f"程序名称包含非法字符：{name}"
    return None


def assemble_command(base, cfg: BuildConfig):
    """按配置组装完整命令列表（不拼字符串，路径含空格也安全）"""
    cmd = list(base)
    if cfg.onefile:
        cmd.append("--onefile")
    if cfg.windowed:
        cmd.append("--windowed")
    if cfg.noconfirm:
        cmd.append("--noconfirm")
    if cfg.clean:
        cmd.append("--clean")
    if cfg.debug:
        cmd.append(f"--debug={cfg.debug_level.strip() or 'all'}")
    if cfg.icon:
        cmd.append(f"--icon={cfg.icon}")
    if cfg.data:
        cmd.append(f"--add-data={cfg.data}")
    if cfg.hidden:
        for m in re.split(r"[,，\s]+", cfg.hidden.strip()):
            if m:
                cmd.append(f"--hidden-import={m}")
    if cfg.name.strip():
        cmd.append(f"--name={cfg.name.strip()}")
    if cfg.output:
        cmd.append(f"--distpath={cfg.output}")
    cmd.append(cfg.script)
    return cmd


def format_cmd(cmd):
    """仅用于预览/日志显示：含空格的参数加引号"""
    return " ".join(f'"{a}"' if any(c.isspace() for c in a) else a for a in cmd)


def clean_artifacts(cfg: BuildConfig):
    """删除本次构建的中间产物，返回已删除的相对路径列表

    复选框的「清理构建文件」光靠 --clean 做不到：它只在构建前清缓存与 workpath
    内容，构建后 build/<name>/ 会重新生成，.spec 更是从不清理。故打包成功后在此收尾。
    只动本次构建产物，其它项目的 build 子目录与 .spec 保持原样。
    """
    name = os.path.splitext(os.path.basename(cfg.name.strip() or cfg.script))[0]
    if not name.strip("."):  # 空名或 "." / ".." 之类，拒绝删除
        return []
    build_dir = os.path.join("build", name)
    spec = name + ".spec"
    removed = []
    try:
        if os.path.isdir(build_dir):
            shutil.rmtree(build_dir)
            removed.append(build_dir)
            if not os.listdir("build"):  # 本次是最后一个，顺带清掉空的 build
                os.rmdir("build")
        if os.path.isfile(spec):
            os.remove(spec)
            removed.append(spec)
    except OSError:
        pass  # 文件被占用/无权限时留着，不影响打包结果
    return removed


if __name__ == "__main__":
    # 自检：只删本次构建产物，不碰其它项目的中间产物
    import tempfile

    _cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as _d:
        os.chdir(_d)
        os.makedirs(os.path.join("build", "demo"))
        os.makedirs(os.path.join("build", "其它"))
        open("demo.spec", "w").close()
        open("其它.spec", "w").close()
        _removed = clean_artifacts(BuildConfig(script="demo.py"))
        assert _removed == [os.path.join("build", "demo"), "demo.spec"], _removed
        assert not os.path.exists(os.path.join("build", "demo"))
        assert os.path.isdir(os.path.join("build", "其它"))
        assert os.path.isfile("其它.spec")
        os.chdir(_cwd)
    print("自检通过")
