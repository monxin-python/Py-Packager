"""脚本内容分析：读取源码并用 AST 检测 input()/getpass() 调用（纯逻辑）"""

import ast
import os


def read_text_file(path):
    """优先 UTF-8 读取，失败时回退到 GBK（中文 Windows 常见编码）"""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="gbk", errors="replace") as f:
            return f.read()


def _is_input_call(node):
    """判断 ast 调用节点是否为 input() / getpass() / getpass.getpass()"""
    if isinstance(node.func, ast.Name) and node.func.id in ("input", "getpass"):
        return True
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "getpass"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "getpass"
    )


def check_input_functions(path):
    """用 AST 检测真实的 input()/getpass() 调用，避免注释、字符串误报"""
    if not path or not os.path.isfile(path):
        return False
    try:
        tree = ast.parse(read_text_file(path))
    except (OSError, SyntaxError):
        return False
    return any(
        isinstance(n, ast.Call) and _is_input_call(n) for n in ast.walk(tree)
    )
