"""打包执行：在后台线程运行 PyInstaller，通过队列把输出交给 GUI（不直接操作 GUI）"""

import os
import queue
import subprocess
import threading


class BuildProcess:
    """管理一次打包任务：启动、输出队列、终止"""

    def __init__(self):
        self.queue = queue.Queue()
        self.proc = None
        self._thread = None

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, cmd):
        """在守护线程中执行命令；输出以 (kind, payload) 消息入队

        kind 取值：OUT（一行输出）、DONE（返回码）、ERROR（启动异常信息）
        """
        self._thread = threading.Thread(
            target=self._worker, args=(cmd,), daemon=True
        )
        self._thread.start()

    def terminate(self):
        """终止仍在运行的打包进程"""
        if self.proc is not None:
            self.proc.kill()

    def _worker(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                errors="replace",
                # 防止从 GUI 启动时闪现黑色控制台窗口
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            self.proc = proc
            for line in proc.stdout:
                self.queue.put(("OUT", line))
            proc.wait()
            self.queue.put(("DONE", proc.returncode))
        except Exception as e:
            self.queue.put(("ERROR", str(e)))
        finally:
            self.proc = None
