"""限时自动运行器：自动启用瞄准+射击，跑指定秒数后退出。

与 main.py 不同：无需 F6/F8 热键，启动即启用，到时自动停止，
便于自动化测试与调参。用法：
    python run_test.py [duration_seconds]
"""

import sys
import time

import pydirectinput

from aim_bot.screen_capture import ScreenCapture
from aim_bot.detector import TargetDetector
from aim_bot.aim_assist import AimAssist

# 关闭 failsafe：否则鼠标被移到屏幕角落时 pydirectinput 会抛异常中断
pydirectinput.FAILSAFE = False


def main(duration):
    cap = ScreenCapture()
    detector = TargetDetector()
    aim = AimAssist()

    region = cap.find_window()
    offset_x = region[0] if region else 0
    offset_y = region[1] if region else 0
    if not cap.start(region=region):
        print("[错误] 捕获启动失败")
        return
    screen_center = cap.window_center  # 窗口中心（屏幕坐标）= 准星位置

    from aim_bot.config import (
        AIM_SENSITIVITY, AIM_SMOOTHING, AIM_DEADZONE,
        SHOOT_RANGE, SHOOT_COOLDOWN,
    )
    print(f"[运行器] 启用瞄准，时长 {duration:.0f}s，中心={screen_center}")
    print(f"[参数] SENS={AIM_SENSITIVITY} SMOOTH={AIM_SMOOTHING} DEAD={AIM_DEADZONE} "
          f"RANGE={SHOOT_RANGE} CD={SHOOT_COOLDOWN}")

    # 初始开局点击：CLICK TO BEGIN 界面视角锁定，先点一下启动本局计时，
    # 否则若开局无目标落入射击范围会陷入"不开火→不开局"的死锁。
    time.sleep(0.3)
    pydirectinput.click()
    time.sleep(0.2)

    start = time.time()
    frames = 0
    detect_frames = 0
    no_target_frames = 0

    dists = []          # 每帧最优目标距中心的距离
    band_lt20 = 0       # <20px 帧数
    band_lt40 = 0       # <40px 帧数

    while time.time() - start < duration:
        frame = cap.get_frame()
        if frame is None:
            time.sleep(0.001)
            continue
        frames += 1

        h, w = frame.shape[:2]
        best, _ = detector.detect(frame, w // 2, h // 2)

        if best:
            detect_frames += 1
            tx = best["cx"] + offset_x
            ty = best["cy"] + offset_y
            dist = aim.update(tx, ty, screen_center[0], screen_center[1])
            dists.append(dist)
            if dist < 20:
                band_lt20 += 1
            if dist < 40:
                band_lt40 += 1
        else:
            no_target_frames += 1
            aim.clear_smoothing()

    elapsed = time.time() - start
    cap.stop()

    fps = frames / elapsed if elapsed else 0
    print("-" * 50)
    print(f"[统计] 时长={elapsed:.1f}s 帧={frames} FPS={fps:.1f}")
    print(f"[统计] 有目标帧={detect_frames} 无目标帧={no_target_frames}")
    print(f"[统计] 射击次数={aim.shots_fired}")
    if dists:
        dists_sorted = sorted(dists)
        n = len(dists_sorted)
        print(f"[距离] 最小={min(dists):.0f} 中位={dists_sorted[n//2]:.0f} "
              f"最大={max(dists):.0f} 均值={sum(dists)/n:.0f}")
        print(f"[距离] <20px 帧={band_lt20}({100*band_lt20/n:.0f}%) "
              f"<40px 帧={band_lt40}({100*band_lt40/n:.0f}%)")


if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    main(dur)
