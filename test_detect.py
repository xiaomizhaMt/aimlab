"""检测链路自测脚本（只读，不移动鼠标、不射击）。

用途：在 Aim Lab 实际画面上验证「屏幕捕获 + 颜色检测」是否正常，
而不让程序接管鼠标。运行约 6 秒后自动退出并打印统计。
"""

import time

from aim_bot.screen_capture import ScreenCapture
from aim_bot.detector import TargetDetector, get_center_of_frame


def main(duration=6.0):
    cap = ScreenCapture()
    detector = TargetDetector()

    # 尝试定位 Aim Lab 窗口；失败则全屏捕获
    region = cap.find_window()
    if not cap.start(region=region):
        print("[错误] 屏幕捕获启动失败")
        return

    print(f"[信息] 开始检测自测，持续 {duration:.0f} 秒 ...")
    start = time.time()
    frames = 0
    hit_frames = 0          # 至少检测到一个目标的帧数
    max_targets = 0
    sample_printed = 0

    while time.time() - start < duration:
        frame = cap.get_frame()
        if frame is None:
            time.sleep(0.001)
            continue

        frames += 1
        cx, cy = get_center_of_frame(frame)
        best, all_targets = detector.detect(frame, cx, cy)

        if all_targets:
            hit_frames += 1
            max_targets = max(max_targets, len(all_targets))

        # 打印前几次命中样本，便于核对坐标与距离
        if best and sample_printed < 5:
            sample_printed += 1
            print(
                f"  [样本{sample_printed}] 目标数={len(all_targets):2d} "
                f"最优=({best['cx']},{best['cy']}) "
                f"距中心={best['dist']:.0f}px 面积={best['area']:.0f} "
                f"颜色={best['color']}"
            )

    elapsed = time.time() - start
    cap.stop()

    fps = frames / elapsed if elapsed else 0
    print("-" * 50)
    print(f"[统计] 总帧数={frames}  平均FPS={fps:.1f}")
    print(f"[统计] 命中帧={hit_frames}/{frames}  单帧最多目标={max_targets}")
    if hit_frames == 0:
        print("[结论] 未检测到任何青色目标 —— 检查显示模式/颜色范围/检测半径")
    else:
        print("[结论] 检测链路正常工作 ✅")


if __name__ == "__main__":
    main()
