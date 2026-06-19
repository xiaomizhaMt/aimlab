"""一次性诊断：抓一帧真实画面，存盘并分析青色像素分布。

排查检测 0 命中的原因：
- 帧尺寸 -> 确认捕获分辨率
- 存 PNG -> 人工核对捕获的是游戏还是桌面（是否被最小化）
- 全画面青色像素统计 + 包围盒 -> 判断 HSV 范围是否命中、目标距中心多远
"""

import time
import cv2
import numpy as np

from aim_bot.screen_capture import ScreenCapture
from aim_bot.config import TARGET_CYAN_LOWER, TARGET_CYAN_UPPER

cap = ScreenCapture()
region = cap.find_window()
cap.start(region=region)

# 取几帧，丢弃前面可能的空帧
frame = None
for _ in range(30):
    f = cap.get_frame()
    if f is not None:
        frame = f
    time.sleep(0.01)
cap.stop()

if frame is None:
    print("[错误] 未取到帧")
    raise SystemExit

h, w = frame.shape[:2]
cx, cy = w // 2, h // 2
print(f"[帧] 尺寸 = {w} x {h}, 中心 = ({cx},{cy})")

cv2.imwrite("diag_frame.png", frame)
print("[保存] diag_frame.png")

hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, TARGET_CYAN_LOWER, TARGET_CYAN_UPPER)
cnt = int((mask > 0).sum())
print(f"[青色] 当前范围 {TARGET_CYAN_LOWER.tolist()}~{TARGET_CYAN_UPPER.tolist()} "
      f"命中像素 = {cnt}")

if cnt > 0:
    ys, xs = np.where(mask > 0)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    bx, by = (x0 + x1) // 2, (y0 + y1) // 2
    dist = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
    print(f"[青色] 像素包围盒 x[{x0}-{x1}] y[{y0}-{y1}] 形心≈({bx},{by}) 距中心={dist:.0f}px")
    cv2.imwrite("diag_mask.png", mask)
    print("[保存] diag_mask.png")
else:
    # 没命中，扫描画面里实际存在的高饱和色相，帮助校准
    s = hsv[..., 1]
    v = hsv[..., 2]
    sel = (s > 100) & (v > 100)
    if sel.sum() > 0:
        hues = hsv[..., 0][sel]
        vals, counts = np.unique(hues, return_counts=True)
        top = sorted(zip(counts.tolist(), vals.tolist()), reverse=True)[:8]
        print("[校准] 画面中高饱和像素的主要色相(H, OpenCV 0-180) 及像素数:")
        for c, hv in top:
            print(f"        H={hv:3d}  像素={c}")
    else:
        print("[校准] 画面几乎没有高饱和像素 —— 很可能捕获到的是桌面(游戏被最小化)")
