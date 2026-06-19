"""
Aim Lab 自动瞄准射击程序 - 屏幕捕获模块。

使用 DXcam 通过 DirectX 捕获游戏窗口或全屏画面。
"""

import dxcam
import win32gui

try:
    from .config import WINDOW_TITLE
except ImportError:
    from config import WINDOW_TITLE


class ScreenCapture:
    """屏幕捕获器，封装 DXcam 的启动、取帧和释放。"""

    def __init__(self):
        self.camera = None          # DXcam 捕获器实例，未启动时为 None
        self.target_fps = 120       # 目标捕获帧率（高帧率降低检测延迟，提升瞄准吞吐）
        self._window_rect = None    # 当前捕获区域 (left, top, right, bottom)

    def find_window(self):
        """
        查找标题包含 WINDOW_TITLE 的可见窗口。

        Returns:
            tuple | None: 客户区屏幕坐标 (left, top, right, bottom)。
        """
        # 枚举回调：收集标题包含目标关键字的可见窗口句柄
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if WINDOW_TITLE.lower() in title.lower():
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(enum_callback, windows)  # 遍历所有顶层窗口

        if not windows:
            print(f"[警告] 未找到标题包含 '{WINDOW_TITLE}' 的窗口")
            print("[信息] 将使用全屏捕获模式")
            return None

        # 取第一个匹配窗口，换算其客户区在屏幕上的绝对坐标
        hwnd = windows[0]
        rect = win32gui.GetClientRect(hwnd)            # 客户区尺寸 (0,0,宽,高)
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))  # 客户区左上角→屏幕坐标
        right = left + rect[2]
        bottom = top + rect[3]

        print(f"[信息] 找到窗口: '{win32gui.GetWindowText(hwnd)}'")
        print(f"[信息] 窗口区域: left={left}, top={top}, right={right}, bottom={bottom}")
        print(f"[信息] 窗口尺寸: {rect[2]}x{rect[3]}")

        return left, top, right, bottom

    def start(self, region=None):
        """
        启动 DXcam 捕获。

        Args:
            region: 捕获区域 (left, top, right, bottom)，None 表示全屏。

        Returns:
            bool: 是否启动成功。
        """
        if self.camera is not None:
            self.stop()

        try:
            try:
                self.camera = dxcam.create(output_color="BGR")
            except TypeError:
                self.camera = dxcam.create()
        except Exception as exc:
            print(f"[错误] 创建 DXcam 捕获器失败: {exc}")
            return False

        self._window_rect = region

        try:
            if region:
                self.camera.start(
                    target_fps=self.target_fps,
                    region=region,
                    video_mode=True,
                )
                print(f"[信息] 屏幕捕获已启动 (区域模式: {region})")
            else:
                self.camera.start(target_fps=self.target_fps, video_mode=True)
                print("[信息] 屏幕捕获已启动 (全屏模式)")
        except Exception as exc:
            print(f"[错误] 启动屏幕捕获失败: {exc}")
            self.stop()
            return False

        return True

    def get_frame(self):
        """获取最新一帧图像。"""
        if self.camera is None:
            return None
        try:
            return self.camera.get_latest_frame()
        except Exception as exc:
            print(f"[错误] 获取屏幕帧失败: {exc}")
            return None

    def stop(self):
        """停止屏幕捕获并释放 DXcam 资源。"""
        if self.camera is None:
            return

        try:
            self.camera.stop()
        except Exception as exc:
            print(f"[警告] 停止屏幕捕获时出现异常: {exc}")
        finally:
            self.camera = None
            print("[信息] 屏幕捕获已停止")

    @property
    def window_center(self):
        """获取窗口中心点在屏幕上的坐标。"""
        if not self._window_rect:
            return None

        left, top, right, bottom = self._window_rect
        return (left + right) // 2, (top + bottom) // 2

    @property
    def window_size(self):
        """获取窗口宽高。"""
        if not self._window_rect:
            return None

        left, top, right, bottom = self._window_rect
        return right - left, bottom - top

    def __del__(self):
        self.stop()
