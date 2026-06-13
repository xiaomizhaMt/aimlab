"""
Aim Lab 自动瞄准射击程序 - 主程序入口。

整合屏幕捕获、目标检测、瞄准控制和热键监听。
"""

import time

import cv2
import keyboard

try:
    from .config import (
        AIM_SENSITIVITY,
        AIM_SMOOTHING,
        AUTO_SHOOT,
        DETECT_FRAME_SKIP,
        DETECT_RADIUS,
        EXIT_KEY,
        SHOOT_RANGE,
        SHOW_DEBUG,
        TOGGLE_KEY,
    )
    from .aim_assist import AimAssist
    from .detector import TargetDetector
    from .screen_capture import ScreenCapture
except ImportError:
    from config import (
        AIM_SENSITIVITY,
        AIM_SMOOTHING,
        AUTO_SHOOT,
        DETECT_FRAME_SKIP,
        DETECT_RADIUS,
        EXIT_KEY,
        SHOOT_RANGE,
        SHOW_DEBUG,
        TOGGLE_KEY,
    )
    from aim_assist import AimAssist
    from detector import TargetDetector
    from screen_capture import ScreenCapture


class AimBot:
    """自动瞄准主控制器。"""

    def __init__(self):
        # 三大功能模块：屏幕捕获、目标检测、瞄准射击
        self.screen_capture = ScreenCapture()
        self.detector = TargetDetector()
        self.aim_assist = AimAssist()

        self.running = False      # 主循环是否运行中
        self.enabled = False      # 自动瞄准是否开启（由 F6 切换）
        self.frame_count = 0      # 已处理帧计数，用于帧跳跃

        # 捕获区域左上角在屏幕上的偏移，用于把帧内坐标换算成屏幕坐标
        self._offset_x = 0
        self._offset_y = 0
        self._screen_center = None   # 屏幕中心点（瞄准的参照原点）
        self._keyboard_hooks = []    # 已注册的热键钩子，退出时统一注销
        self._cleaned_up = False     # 防止 cleanup 重复执行

    def find_and_start(self):
        """查找 Aim Lab 窗口并启动屏幕捕获。"""
        region = self.screen_capture.find_window()

        if region:
            self._offset_x = region[0]
            self._offset_y = region[1]
        else:
            self._offset_x = 0
            self._offset_y = 0

        if not self.screen_capture.start(region=region):
            raise RuntimeError("屏幕捕获启动失败")

        self._screen_center = self.screen_capture.window_center
        return region is not None

    def run(self):
        """运行主循环。"""
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

        try:
            found = self.find_and_start()
            if not found:
                print("[警告] 未找到 Aim Lab 窗口，将使用全屏捕获")

            self._register_hotkeys()
            self._run_loop()
        except KeyboardInterrupt:
            print("\n[信息] 用户中断")
        except Exception as exc:
            print(f"\n[错误] 程序运行失败: {exc}")
        finally:
            self.cleanup()

    def _register_hotkeys(self):
        """注册热键，失败时抛出明确错误。"""
        try:
            self._keyboard_hooks.append(
                keyboard.on_press_key(TOGGLE_KEY, self._toggle_callback)
            )
            self._keyboard_hooks.append(
                keyboard.on_press_key(EXIT_KEY, self._exit_callback)
            )
        except Exception as exc:
            raise RuntimeError(
                f"热键注册失败，请尝试以管理员权限运行终端: {exc}"
            ) from exc

    def _run_loop(self):
        """主循环：取帧 → 检测 → 瞄准 → 射击，直到 running 置为 False。"""
        self.running = True
        last_fps_time = time.time()   # 上次刷新 FPS 的时间戳
        fps_counter = 0               # 当前 1 秒窗口内累计的帧数
        fps = 0                       # 最近一次统计出的 FPS

        while self.running:
            frame = self.screen_capture.get_frame()

            # 捕获器尚未就绪或暂时无新帧，稍等后重试
            if frame is None:
                time.sleep(0.001)
                continue

            frame_h, frame_w = frame.shape[:2]
            # 全屏模式下窗口中心未知，首帧到达后用画面中心兜底
            if self._screen_center is None:
                self._screen_center = (
                    self._offset_x + frame_w // 2,
                    self._offset_y + frame_h // 2,
                )
                print(f"[信息] 使用捕获画面中心: {self._screen_center}")

            self.frame_count += 1

            now = time.time()
            if now - last_fps_time >= 1.0:
                fps = fps_counter
                fps_counter = 0
                last_fps_time = now

            if self.frame_count % DETECT_FRAME_SKIP != 0:
                continue

            # 仅统计通过帧跳跃、真正进入检测环节的帧，FPS 反映实际处理速率
            fps_counter += 1

            # 未开启自动瞄准时，仅周期性打印待命状态
            if not self.enabled:
                if SHOW_DEBUG and self.frame_count % 30 == 0:
                    self._show_status(fps)
                continue

            # 以帧中心为参照检测目标（检测在帧内坐标系中进行）
            frame_center_x = frame_w // 2
            frame_center_y = frame_h // 2
            best_target, all_targets = self.detector.detect(
                frame, frame_center_x, frame_center_y
            )

            if best_target:
                # 帧内坐标 + 捕获偏移 = 目标在屏幕上的绝对坐标
                target_screen_x = best_target["cx"] + self._offset_x
                target_screen_y = best_target["cy"] + self._offset_y

                distance = self.aim_assist.aim_at(
                    target_screen_x,
                    target_screen_y,
                    self._screen_center[0],
                    self._screen_center[1],
                )

                if self.aim_assist.is_in_shoot_range(distance):
                    self.aim_assist.shoot()
            else:
                # 当前帧没有目标：清空平滑历史，避免旧偏移值滞后影响下次瞄准
                self.aim_assist.clear_smoothing()

            if SHOW_DEBUG:
                self._show_debug(frame, best_target, all_targets, fps)

    def _toggle_callback(self, event):
        """热键回调：切换自动瞄准开关。"""
        self.enabled = not self.enabled
        if self.enabled:
            self.aim_assist.reset()
            print(f"\n[+] 自动瞄准已开启 (按下 {TOGGLE_KEY} 关闭)")
        else:
            print(f"\n[-] 自动瞄准已关闭 (按下 {TOGGLE_KEY} 开启)")

    def _exit_callback(self, event):
        """热键回调：退出程序。"""
        print("\n[信息] 正在退出...")
        self.running = False

    def _show_status(self, fps):
        """显示待命状态。"""
        stats = self.aim_assist.get_stats()
        print(f"\r[待命] FPS: {fps} | 已射击: {stats['shots_fired']}", end="")

    def _show_debug(self, frame, best_target, all_targets, fps):
        """显示 OpenCV 调试窗口。"""
        stats = self.aim_assist.get_stats()
        display = frame.copy()

        status = "ON" if self.enabled else "OFF"
        cv2.putText(
            display,
            f"Status: {status}",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0) if self.enabled else (0, 0, 255),
            2,
        )
        cv2.putText(
            display,
            f"FPS: {fps}",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )
        cv2.putText(
            display,
            f"Shots: {stats['shots_fired']}",
            (10, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )
        cv2.putText(
            display,
            f"Targets: {len(all_targets)}",
            (10, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )

        if best_target:
            cv2.circle(display, (best_target["cx"], best_target["cy"]), 8, (0, 0, 255), 2)

        cv2.putText(
            display,
            f"[{TOGGLE_KEY}] Toggle",
            (10, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )
        cv2.imshow("Aim Bot Debug", display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.running = False

    def cleanup(self):
        """释放资源，允许重复调用。"""
        if self._cleaned_up:
            return
        self._cleaned_up = True

        for hook in self._keyboard_hooks:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass
        self._keyboard_hooks.clear()

        self.screen_capture.stop()
        cv2.destroyAllWindows()
        print("[信息] 资源已释放")
        print(f"[统计] 总射击次数: {self.aim_assist.shots_fired}")


def main():
    bot = AimBot()
    bot.run()


if __name__ == "__main__":
    main()
