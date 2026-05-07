"""
Aim Lab 自动瞄准射击程序 - 瞄准与射击控制模块
使用 PyDirectInput 实现游戏内鼠标控制
"""

import time
import numpy as np
from collections import deque

import pydirectinput
from config import (
    AIM_SENSITIVITY, AIM_SMOOTHING, AIM_DEADZONE,
    SHOOT_RANGE, SHOOT_COOLDOWN, AUTO_SHOOT
)


class AimAssist:
    """瞄准与射击控制器"""

    def __init__(self):
        # 平滑移动历史队列
        self._smooth_history = deque(maxlen=max(AIM_SMOOTHING, 1))

        # 射击冷却计时
        self._last_shot_time = 0

        # 累计统计
        self.shots_fired = 0
        self.targets_hit = 0

        # 设置 PyDirectInput 的默认延迟
        pydirectinput.PAUSE = 0.0

    def aim_at(self, target_cx, target_cy, screen_center_x, screen_center_y):
        """瞄准目标

        计算目标到屏幕中心的偏移量，平滑移动鼠标

        Args:
            target_cx: 目标中心 x（屏幕坐标）
            target_cy: 目标中心 y（屏幕坐标）
            screen_center_x: 屏幕中心 x
            screen_center_y: 屏幕中心 y

        Returns:
            float: 目标到屏幕中心的距离（像素）
        """
        # 计算偏移量
        dx = target_cx - screen_center_x
        dy = target_cy - screen_center_y

        distance = np.sqrt(dx ** 2 + dy ** 2)

        # 死区检测：目标已经在屏幕中心附近，不移动鼠标
        if distance < AIM_DEADZONE:
            return distance

        # 应用灵敏度
        move_x = int(dx * AIM_SENSITIVITY)
        move_y = int(dy * AIM_SENSITIVITY)

        # 平滑处理：移动平均
        self._smooth_history.append((move_x, move_y))

        if len(self._smooth_history) > 1:
            avg_x = int(np.mean([m[0] for m in self._smooth_history]))
            avg_y = int(np.mean([m[1] for m in self._smooth_history]))
        else:
            avg_x, avg_y = move_x, move_y

        # 应用鼠标移动（相对移动）
        if avg_x != 0 or avg_y != 0:
            pydirectinput.moveRel(avg_x, avg_y, relative=True)

        return distance

    def shoot(self):
        """执行射击

        Returns:
            bool: 是否成功射击
        """
        if not AUTO_SHOOT:
            return False

        current_time = time.time()

        # 检查冷却时间
        if current_time - self._last_shot_time < SHOOT_COOLDOWN:
            return False

        # 执行射击（鼠标按下 + 释放）
        pydirectinput.mouseDown(button='left')
        time.sleep(0.02)  # 短暂的按下时间
        pydirectinput.mouseUp(button='left')

        self._last_shot_time = current_time
        self.shots_fired += 1

        return True

    def is_in_shoot_range(self, distance):
        """检查目标是否在射击范围内

        Args:
            distance: 目标到屏幕中心的距离（像素）

        Returns:
            bool: 是否应该射击
        """
        return distance <= SHOOT_RANGE

    def reset(self):
        """重置状态"""
        self._smooth_history.clear()
        self._last_shot_time = 0

    def get_stats(self):
        """获取统计信息"""
        return {
            "shots_fired": self.shots_fired,
            "targets_hit": self.targets_hit,
        }
