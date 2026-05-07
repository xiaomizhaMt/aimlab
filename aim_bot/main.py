"""
Aim Lab 自动瞄准射击程序 - 主程序入口
整合所有模块，运行主循环
"""

import time
import sys

import keyboard
import cv2
import numpy as np
import win32gui
import win32con

from config import (
    TOGGLE_KEY, EXIT_KEY, DETECT_FRAME_SKIP,
    SHOW_DEBUG, SHOOT_RANGE, DETECT_RADIUS,
    AIM_SENSITIVITY, AIM_SMOOTHING, AIM_DEADZONE,
    AUTO_SHOOT, SHOOT_COOLDOWN
)
from screen_capture import ScreenCapture
from detector import TargetDetector, get_center_of_frame
from aim_assist import AimAssist


class AimBot:
    """自动瞄准机器人主控制器"""

    def __init__(self):
        self.screen_capture = ScreenCapture()
        self.detector = TargetDetector()
        self.aim_assist = AimAssist()

        self.running = False
        self.enabled = False
        self.frame_count = 0

        # 窗口偏移量（用于将帧内坐标转换为屏幕坐标）
        self._offset_x = 0
        self._offset_y = 0

    def find_and_start(self):
        """查找 Aim Lab 窗口并启动捕获"""
        region = self.screen_capture.find_window()

        # 记录窗口偏移
        if region:
            self._offset_x = region[0]
            self._offset_y = region[1]

        self.screen_capture.start(region=region)

        # 获取窗口中心（屏幕坐标）
        self._screen_center = self.screen_capture.window_center
        if self._screen_center is None:
            # 如果没有找到窗口，使用主显示器中心
            self._screen_center = (960, 540)
            print("[信息] 使用默认屏幕中心 (960, 540)")

        return region is not None

    def run(self):
        """运行主循环"""
        print("=" * 50)
        print("  Aim Lab 自动瞄准射击程序")
        print("=" * 50)
        print(f"[信息] 按 {TOGGLE_KEY} 启动/停止自动瞄准")
        print(f"[信息] 按 {EXIT_KEY} 退出程序")
        print(f"[信息] 灵敏度: {AIM_SENSITIVITY}")
        print(f"[信息] 平滑度: {AIM_SMOOTHING}")
        print(f"[信息] 检测范围: {DETECT_RADIUS}px")
        print(f"[信息] 射击范围: {SHOOT_RANGE}px")
        print(f"[信息] 自动射击: {'开启' if AUTO_SHOOT else '关闭'}")
        print("-" * 50)

        # 查找窗口并启动捕获
        found = self.find_and_start()
        if not found:
            print("[警告] 未找到 Aim Lab 窗口，将使用全屏捕获")

        # 注册热键
        keyboard.on_press_key(TOGGLE_KEY, self._toggle_callback)
        keyboard.on_press_key(EXIT_KEY, self._exit_callback)

        self.running = True
        last_fps_time = time.time()
        fps_counter = 0
        fps = 0

        try:
            while self.running:
                frame = self.screen_capture.get_frame()

                if frame is None:
                    time.sleep(0.001)
                    continue

                self.frame_count += 1
                fps_counter += 1

                # 计算 FPS
                now = time.time()
                if now - last_fps_time >= 1.0:
                    fps = fps_counter
                    fps_counter = 0
                    last_fps_time = now

                # 帧跳跃优化
                if self.frame_count % DETECT_FRAME_SKIP != 0:
                    continue

                if not self.enabled:
                    # 未启用时只显示调试信息
                    if SHOW_DEBUG and self.frame_count % 30 == 0:
                        self._show_status(frame, fps)
                    continue

                # ====== 核心瞄准逻辑 ======
                frame_h, frame_w = frame.shape[:2]
                frame_center_x = frame_w // 2
                frame_center_y = frame_h // 2

                # 检测目标
                best_target, all_targets = self.detector.detect(
                    frame, frame_center_x, frame_center_y
                )

                if best_target:
                    # 计算帧内目标坐标到屏幕坐标的转换
                    target_screen_x = best_target["cx"] + self._offset_x
                    target_screen_y = best_target["cy"] + self._offset_y

                    # 执行瞄准
                    distance = self.aim_assist.aim_at(
                        target_screen_x, target_screen_y,
                        self._screen_center[0], self._screen_center[1]
                    )

                    # 如果在射击范围内，执行射击
                    if self.aim_assist.is_in_shoot_range(distance):
                        if self.aim_assist.shoot():
                            pass  # 射击成功

                # 调试显示
                if SHOW_DEBUG:
                    self._show_debug(frame, best_target, fps)

        except KeyboardInterrupt:
            print("\n[信息] 用户中断")
        finally:
            self.cleanup()

    def _toggle_callback(self, event):
        """热键回调：切换自动瞄准开关"""
        self.enabled = not self.enabled
        if self.enabled:
            self.aim_assist.reset()
            print(f"\n[+] 自动瞄准已开启 (按下 {TOGGLE_KEY} 关闭)")
        else:
            print(f"\n[-] 自动瞄准已关闭 (按下 {TOGGLE_KEY} 开启)")

    def _exit_callback(self, event):
        """热键回调：退出程序"""
        print("\n[信息] 正在退出...")
        self.running = False

    def _show_status(self, frame, fps):
        """显示状态信息"""
        stats = self.aim_assist.get_stats()
        h, w = frame.shape[:2]
        print(f"\r[待命] FPS: {fps} | 已射击: {stats['shots_fired']}", end="")

    def _show_debug(self, frame, best_target, fps):
        """显示调试信息"""
        stats = self.aim_assist.get_stats()

        # 复制帧用于显示
        display = frame.copy()

        # 信息叠加
        status = "ON" if self.enabled else "OFF"
        cv2.putText(display, f"Status: {status}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 255, 0) if self.enabled else (0, 0, 255), 2)
        cv2.putText(display, f"FPS: {fps}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(display, f"Shots: {stats['shots_fired']}", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # 显示开关提示
        cv2.putText(display, f"[{TOGGLE_KEY}] Toggle", (10, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Aim Bot Debug", display)

        # 检查窗口关闭
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.running = False

    def cleanup(self):
        """清理资源"""
        self.screen_capture.stop()
        cv2.destroyAllWindows()
        print("[信息] 资源已释放")
        print(f"[统计] 总射击次数: {self.aim_assist.shots_fired}")


def main():
    """主函数"""
    bot = AimBot()
    bot.run()


if __name__ == "__main__":
    main()
