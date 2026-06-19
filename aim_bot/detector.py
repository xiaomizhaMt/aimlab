"""
Aim Lab 自动瞄准射击程序 - 目标检测模块
使用 OpenCV HSV 颜色过滤识别靶标
"""

import cv2
import numpy as np

try:
    from .config import (
        TARGET_COLORS, DETECT_RADIUS, SHOOT_RANGE, SHOW_DEBUG, DETECT_SCALE,
    )
except ImportError:
    from config import (
        TARGET_COLORS, DETECT_RADIUS, SHOOT_RANGE, SHOW_DEBUG, DETECT_SCALE,
    )


class TargetDetector:
    """目标检测器，通过颜色识别定位靶标"""

    def __init__(self):
        # 缓存帧计数，用于帧跳跃优化
        self._frame_count = 0

    def detect(self, frame, center_x, center_y):
        """
        在帧中检测目标。

        核心检测流程：
        1. BGR -> HSV 颜色空间转换（颜色过滤更稳定）
        2. 对每种配置的颜色创建掩码
        3. 形态学操作去除噪声
        4. 查找轮廓并筛选有效目标
        5. 综合评分选出最优目标

        Args:
            frame: 输入帧 (numpy.ndarray, BGR格式)
            center_x: 屏幕中心 x 坐标（相对于帧）
            center_y: 屏幕中心 y 坐标（相对于帧）

        Returns:
            tuple: (best_target, targets)
                - best_target: 最优目标 dict {'cx','cy','dist','color',...} 或 None
                - targets: 所有检测到的目标列表
        """
        if frame is None:
            return None, []

        self._frame_count += 1

        # 检测前缩放：把画面缩小到 DETECT_SCALE 再做 cv2 处理，处理量按平方下降，
        # 大幅提升循环帧率、降低瞄准延迟。坐标最后换算回原分辨率。
        s = DETECT_SCALE
        if s != 1.0:
            proc = cv2.resize(frame, None, fx=s, fy=s,
                              interpolation=cv2.INTER_NEAREST)
        else:
            proc = frame

        # 中心、半径、最小面积换算到缩放空间
        scx = center_x * s
        scy = center_y * s
        radius_s = DETECT_RADIUS * s
        min_area_s = max(5.0, 20 * s * s)  # 原始 20px 面积阈值按缩放换算
        inv = 1.0 / s

        # 转换到 HSV 颜色空间
        # HSV 相比 BGR 的优势：色相(H)不受光照变化影响，颜色过滤更稳定
        hsv = cv2.cvtColor(proc, cv2.COLOR_BGR2HSV)

        all_targets = []

        # 对每种配置的颜色进行检测
        for color_name, lower, upper in TARGET_COLORS:
            # 创建颜色掩码：在范围内的像素为白色(255)，其余为黑色(0)
            mask = cv2.inRange(hsv, lower, upper)

            # 形态学操作：去噪和平滑
            # MORPH_OPEN (先腐蚀后膨胀)：去除白色噪点
            # MORPH_CLOSE (先膨胀后腐蚀)：填充目标内部空洞
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

            # 查找轮廓：提取白色区域的边界
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area_s = cv2.contourArea(contour)
                # 过滤太小的噪声（缩放空间阈值）
                if area_s < min_area_s:
                    continue

                # 获取外接矩形和中心点坐标（缩放空间）
                x_s, y_s, w_s, h_s = cv2.boundingRect(contour)
                cx_s = x_s + w_s / 2
                cy_s = y_s + h_s / 2

                # 限制在检测区域内（缩放空间内比较，避免重复换算）
                dist_s = np.sqrt((cx_s - scx) ** 2 + (cy_s - scy) ** 2)
                if dist_s > radius_s:
                    continue

                # 坐标换算回原分辨率，供下游瞄准使用
                all_targets.append({
                    "cx": int(cx_s * inv),          # 目标中心 x（原分辨率帧内坐标）
                    "cy": int(cy_s * inv),          # 目标中心 y
                    "x": int(x_s * inv),            # 外接矩形左上角 x
                    "y": int(y_s * inv),            # 外接矩形左上角 y
                    "w": int(w_s * inv),            # 外接矩形宽度
                    "h": int(h_s * inv),            # 外接矩形高度
                    "area": area_s * inv * inv,     # 目标面积（原分辨率像素数）
                    "dist": dist_s * inv,           # 到屏幕中心的距离（原分辨率）
                    "color": color_name             # 颜色名称
                })

        # 选择最优目标：综合考虑距离和面积进行评分
        best_target = self._select_best_target(all_targets, center_x, center_y)

        # 调试显示（SHOW_DEBUG=True 时显示检测可视化窗口）
        if SHOW_DEBUG:
            self._draw_debug(frame, all_targets, best_target,
                             center_x, center_y)

        return best_target, all_targets

    def _select_best_target(self, targets, center_x, center_y):
        """
        从多个目标中选择最优目标 —— 纯最近原则。

        Gridshot 等密集靶场，靶子大小相近，选「离准星最近」的目标可最小化转场
        距离/时间，吞吐最高（面积加权会偶尔选到稍远的大靶，增加无谓转场）。

        Returns:
            dict | None: 最优目标，无目标时返回 None
        """
        if not targets:
            return None

        best = None
        best_score = float("inf")

        for t in targets:
            # 纯按到准星的距离选最近目标
            score = t["dist"]

            if score < best_score:
                best_score = score
                best = t

        return best

    def _draw_debug(self, frame, targets, best_target, center_x, center_y):
        """绘制调试可视化信息（仅 SHOW_DEBUG=True 时调用）"""
        # 绘制检测区域圆圈
        cv2.circle(frame, (center_x, center_y), DETECT_RADIUS,
                   (0, 255, 0), 1)

        # 绘制所有检测到的目标（外接矩形 + 中心点）
        for t in targets:
            # 不同颜色用不同框色
            color_map = {
                "orange": (0, 165, 255),
                "green": (0, 255, 0),
                "red1": (0, 0, 255),
                "red2": (0, 0, 255),
                "blue": (255, 0, 0),
            }
            color = color_map.get(t["color"], (255, 255, 255))
            cv2.rectangle(frame, (t["x"], t["y"]),
                          (t["x"] + t["w"], t["y"] + t["h"]), color, 1)
            cv2.circle(frame, (t["cx"], t["cy"]), 3, color, -1)

        # 标注最优目标
        if best_target:
            # 红色大圆圈标记最优目标
            cv2.circle(frame, (best_target["cx"], best_target["cy"]),
                       8, (0, 0, 255), 2)
            # 绘制射击范围示意圈
            cv2.circle(frame, (best_target["cx"], best_target["cy"]),
                       SHOOT_RANGE, (0, 0, 255), 1)

            # 显示目标信息
            info = f"target: {best_target['color']}  dist={best_target['dist']:.0f}px"
            cv2.putText(frame, info, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 显示检测到的目标数量
        cv2.putText(frame, f"detected: {len(targets)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 绘制十字准星
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y),
                 (0, 255, 0), 1)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20),
                 (0, 255, 0), 1)


def get_center_of_frame(frame):
    """获取图像帧的中心像素坐标"""
    if frame is None:
        return 0, 0
    height, width = frame.shape[:2]
    return width // 2, height // 2
