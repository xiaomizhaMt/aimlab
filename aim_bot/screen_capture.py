"""
Aim Lab 自动瞄准射击程序 - 屏幕捕获模块
使用 DXcam 高性能 DirectX 屏幕捕获
"""

import dxcam
import win32gui
import win32con
from config import WINDOW_TITLE


class ScreenCapture:
    """
    屏幕捕获器，封装 DXcam 实现高性能截图。

    DXcam 使用 Windows DirectX API 抓取屏幕，相比传统方法：
    - 帧率更高（可达 60-240 FPS）
    - CPU 占用更低
    - 支持区域捕获，减少处理数据量
    """

    def __init__(self):
        self.camera = None          # DXcam 相机对象
        self.target_fps = 60        # 目标捕获帧率
        self._window_rect = None    # 缓存的窗口区域 (left, top, right, bottom)

    def find_window(self):
        """
        遍历系统窗口，找到 Aim Lab 游戏窗口。

        通过 win32gui.EnumWindows 枚举所有顶层窗口，
        匹配标题包含 WINDOW_TITLE 的窗口。

        Returns:
            tuple | None: 窗口区域 (left, top, right, bottom)，未找到返回 None
        """
        def enum_callback(hwnd, windows):
            """EnumWindows 回调函数：收集匹配的窗口句柄"""
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if WINDOW_TITLE.lower() in title.lower():
                    windows.append(hwnd)
            return True  # 继续枚举

        windows = []
        win32gui.EnumWindows(enum_callback, windows)

        if not windows:
            print(f"[警告] 未找到标题包含 '{WINDOW_TITLE}' 的窗口")
            print("[信息] 将使用全屏捕获模式")
            return None

        hwnd = windows[0]
        # 获取窗口客户区矩形（不包括标题栏和边框）
        rect = win32gui.GetClientRect(hwnd)
        # 将客户区左上角坐标转换为屏幕坐标
        left, top = win32gui.ClientToScreen(hwnd, (0, 0))
        right = left + rect[2]   # left + 宽度
        bottom = top + rect[3]   # top + 高度

        print(f"[信息] 找到窗口: '{win32gui.GetWindowText(hwnd)}'")
        print(f"[信息] 窗口区域: left={left}, top={top}, right={right}, bottom={bottom}")
        print(f"[信息] 窗口尺寸: {rect[2]}x{rect[3]}")

        return (left, top, right, bottom)

    def start(self, region=None):
        """
        启动 DXcam 屏幕捕获。

        Args:
            region: 捕获区域 (left, top, right, bottom)，None 表示全屏捕获
        """
        if self.camera is not None:
            self.stop()

        # 创建 DXcam 实例（每个实例可以独立捕获不同区域）
        self.camera = dxcam.create()
        self._window_rect = region

        # video_mode=True 保证持续捕获最新帧
        if region:
            self.camera.start(target_fps=self.target_fps, region=region,
                              video_mode=True)
            print(f"[信息] 屏幕捕获已启动 (区域模式: {region})")
        else:
            self.camera.start(target_fps=self.target_fps, video_mode=True)
            print("[信息] 屏幕捕获已启动 (全屏模式)")

    def get_frame(self):
        """
        获取最新一帧图像。

        DXcam 的 get_latest_frame() 返回最新可用帧，
        而不是排队等待下一帧，保证实时性。

        Returns:
            numpy.ndarray | None: BGR 格式的图像，无新帧时返回 None
        """
        if self.camera is None:
            return None
        return self.camera.get_latest_frame()

    def stop(self):
        """停止屏幕捕获，释放 DXcam 资源"""
        if self.camera is not None:
            self.camera.stop()
            self.camera = None
            print("[信息] 屏幕捕获已停止")

    @property
    def window_center(self):
        """获取窗口中心点在屏幕上的坐标 (x, y)"""
        if self._window_rect:
            left, top, right, bottom = self._window_rect
            cx = (left + right) // 2
            cy = (top + bottom) // 2
            return cx, cy
        return None

    @property
    def window_size(self):
        """获取窗口的宽高尺寸 (width, height)"""
        if self._window_rect:
            left, top, right, bottom = self._window_rect
            return (right - left, bottom - top)
        return None

    def __del__(self):
        """析构时自动释放屏幕捕获资源"""
        self.stop()
