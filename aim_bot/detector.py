"""
Aim Lab 自动瞄准射击程序 - 目标检测模块
使用 OpenCV HSV 颜色过滤识别靶标
"""

import cv2
import numpy as np
from config import (
    TARGET_COLORS, DETECT_RADIUS, SHOOT_RANGE, SHOW_DEBUG
)


class TargetDetector:
    """目标检测器，通过颜色识别定位靶标"""

    def __init__(self):
        # 缓存帧计数，用于帧跳跃优化
        self._frame_count = 0

    def detect(self, frame, center_x, center_y):
        """在帧中检测目标

        Args:
            frame: 输入帧 (numpy.ndarray, BGR格式)
            center_x: 屏幕中心 x 坐标（相对于帧）
            center_y: 屏幕中心 y 坐标（相对于帧）

        Returns:
            tuple: (best_target, targets)
                - best_target: 最优目标 (x, y, area, color_name) 或 None
                - targets: 所有检测到的目标列表
        """
        if frame is None:
            return None, []

        self._frame_count += 1
        height, width = frame.shape[:2]

        # 转换到 HSV 颜色空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        all_targets = []

        # 对每种配置的颜色进行检测
        for color_name, lower, upper in TARGET_COLORS:
            # 创建颜色掩码
            mask = cv2.inRange(hsv, lower, upper)

            # 形态学操作：去噪
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                area = cv2.contourArea(contour)
                # 过滤太小的噪声
                if area < 20:
                    continue

                # 获取外接矩形和中心点
                x, y, w, h = cv2.boundingRect(contour)
                cx = x + w // 2
                cy = y + h // 2

                # 限制在检测区域内（屏幕中心一定半径内）
                dist = np.sqrt((cx - center_x) ** 2 + (cy - center_y) ** 2)
                if dist > DETECT_RADIUS:
                    continue

                all_targets.append({
                    "cx": cx,
                    "cy": cy,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "area": area,
                    "dist": dist,
                    "color": color_name
                })

        # 选择最优目标：距离屏幕中心最近 + 面积大的综合评分
        best_target = self._select_best_target(all_targets, center_x, center_y)

        # 调试显示
        if SHOW_DEBUG:
            self._draw_debug(frame, all_targets, best_target,
                             center_x, center_y)

        return best_target, all_targets

    def _select_best_target(self, targets, center_x, center_y):
        """选择最优目标（综合考虑距离和面积）"""
        if not targets:
            return None

        # 评分规则：距离越近越好，面积适中更好
        # 归一化距离和面积后加权
        max_dist = max(t["dist"] for t in targets) if targets else 1
        max_area = max(t["area"] for t in targets) if targets else 1

        best = None
        best_score = float("inf")

        for t in targets:
            # 距离权重 0.8，面积权重 0.2（越近越好，越大越好）
            dist_score = t["dist"] / max_dist
            area_score = 1 - (t["area"] / max_area)  # 取反，面积大分值低
            score = dist_score * 0.8 + area_score * 0.2

            if score < best_score:
                best_score = score
                best = t

        return best

    def _draw_debug(self, frame, targets, best_target, center_x, center_y):
        """绘制调试信息"""
        # 绘制检测区域圆圈
        cv2.circle(frame, (center_x, center_y), DETECT_RADIUS,
                   (0, 255, 0), 1)

        # 绘制所有检测到的目标
        for t in targets:
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
            cv2.circle(frame, (best_target["cx"], best_target["cy"]),
                       8, (0, 0, 255), 2)

            # 绘制射击范围
            cv2.circle(frame, (best_target["cx"], best_target["cy"]),
                       SHOOT_RANGE, (0, 0, 255), 1)

            # 显示目标信息
            info = f"{best_target['color']} target dist={best_target['dist']:.0f}px"
            cv2.putText(frame, info, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 显示目标数量
        cv2.putText(frame, f"Targets: {len(targets)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 显示十字准星
        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y),
                 (0, 255, 0), 1)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20),
                 (0, 255, 0), 1)


def get_center_of_frame(frame):
    """获取帧的中心点坐标"""
    if frame is None:
        return 0, 0
    height, width = frame.shape[:2]
    return width // 2, height // 2
