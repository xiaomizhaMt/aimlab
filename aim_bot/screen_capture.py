"""
Aim Lab 自动瞄准射击程序 - 屏幕捕获模块
使用 DXcam 高性能 DirectX 屏幕捕获
"""

import dxcam
import win32gui
import win32con
from config import WINDOW_TITLE


class ScreenCapture:
    """屏幕捕获器，封装 DXcam 实现高性能截图"""

    def __init__(self):
        self.camera = None
        self.target_fps = 60
        self._window_rect = None  # 缓存窗口区域

    def find_window(self):
        """查找 Aim Lab 游戏窗口，返回窗口区域 (left, top, right, bottom)"""
        def enum_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if WINDOW_TITLE.lower() in title.lower():
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(enum_callback, windows)

        if not windows:
            print(f"[警告] 未找到标题包含 '{WINDOW_TITLE}' 的窗口")
            print("[信息] 将使用全屏捕获模式")
            return None

        hwnd = windows[0]
        # 获取窗口客户区矩形
        rect = win32gui.GetClientRect(hwnd)
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        right = left + rect[2]
        bottom = top + rect[3]

        print(f"[信息] 找到窗口: '{win32gui.GetWindowText(hwnd)}'")
        print(f"[信息] 窗口区域: left={left}, top={top}, right={right}, bottom={bottom}")
        print(f"[信息] 窗口尺寸: {rect[2]}x{rect[3]}")

        return (left, top, right, bottom)

    def start(self, region=None):
        """启动屏幕捕获

        Args:
            region: 捕获区域 (left, top, right, bottom)，None 表示全屏
        """
        if self.camera is not None:
            self.stop()

        self.camera = dxcam.create()
        self._window_rect = region

        if region:
            self.camera.start(target_fps=self.target_fps, region=region,
                              video_mode=True)
            print(f"[信息] 屏幕捕获已启动 (区域模式: {region})")
        else:
            self.camera.start(target_fps=self.target_fps, video_mode=True)
            print("[信息] 屏幕捕获已启动 (全屏模式)")

    def get_frame(self):
        """获取一帧图像

        Returns:
            numpy.ndarray 或 None（如果无新帧）
        """
        if self.camera is None:
            return None
        return self.camera.get_latest_frame()

    def stop(self):
        """停止屏幕捕获"""
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
            print("[信息] 屏幕捕获已停止")

    @property
    def window_center(self):
        """获取窗口中心点坐标 (x, y)"""
        if self._window_rect:
            left, top, right, bottom = self._window_rect
            cx = (left + right) // 2
            cy = (top + bottom) // 2
            return cx, cy
        return None

    @property
    def window_size(self):
        """获取窗口尺寸 (width, height)"""
        if self._window_rect:
            left, top, right, bottom = self._window_rect
            return (right - left, bottom - top)
        return None

    def __del__(self):
        self.stop()
