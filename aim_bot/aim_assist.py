"""
Aim Lab 自动瞄准射击程序 - 瞄准与射击控制模块
使用 PyDirectInput 实现游戏内鼠标控制
"""

import time
import numpy as np
from collections import deque

import pydirectinput

try:
    from .config import (
        AIM_DEADZONE,
        AIM_FAR_BOOST,
        AIM_FAR_THRESHOLD,
        AIM_SENSITIVITY,
        AIM_SMOOTHING,
        AUTO_SHOOT,
        SHOOT_COOLDOWN,
        SHOOT_RANGE,
    )
except ImportError:
    from config import (
        AIM_DEADZONE,
        AIM_FAR_BOOST,
        AIM_FAR_THRESHOLD,
        AIM_SENSITIVITY,
        AIM_SMOOTHING,
        AUTO_SHOOT,
        SHOOT_COOLDOWN,
        SHOOT_RANGE,
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
        # 计算目标相对屏幕中心的水平/垂直偏移量（带正负，表示方向）
        dx = target_cx - screen_center_x
        dy = target_cy - screen_center_y

        # 欧氏距离：目标离准星有多远
        distance = np.sqrt(dx ** 2 + dy ** 2)

        # 死区检测：目标已经在屏幕中心附近，不移动鼠标
        if distance < AIM_DEADZONE:
            return distance

        # 自适应增益：远距离放大灵敏度加快转场，靠近后用基础灵敏度保证精度
        gain = AIM_SENSITIVITY
        if distance > AIM_FAR_THRESHOLD:
            gain *= AIM_FAR_BOOST

        # 应用灵敏度倍数，得到本帧期望的鼠标移动量
        move_x = int(dx * gain)
        move_y = int(dy * gain)

        # 平滑处理：把最近几帧的移动量做移动平均，削弱抖动、避免过冲
        self._smooth_history.append((move_x, move_y))

        if len(self._smooth_history) > 1:
            avg_x = int(np.mean([m[0] for m in self._smooth_history]))
            avg_y = int(np.mean([m[1] for m in self._smooth_history]))
        else:
            avg_x, avg_y = move_x, move_y

        # 应用鼠标移动（相对移动）
        # 必须 relative=True：发送原始相对位移事件，FPS 游戏的 Raw Input 才能
        # 接收并转动视角；默认 relative=False 会走绝对定位(SetCursorPos)，
        # 在锁定光标的游戏里不产生任何视角旋转。
        if avg_x != 0 or avg_y != 0:
            pydirectinput.moveRel(avg_x, avg_y, relative=True)

        return distance

    def update(self, target_cx, target_cy, screen_center_x, screen_center_y):
        """每帧处理目标：在射击范围内先开火，然后**始终**朝靶心继续收敛。

        要点：
        - 开火基于当前检测到的位置，且在移动之前进行，避免「移动过冲后开火脱靶」。
        - 无论是否开火都继续 aim_at 朝靶心移动（aim_at 内含死区，靠近后自然停住），
          避免「停在靶边缘一直空射」——准星会持续收敛到球心再稳定命中。
        - 单调收敛、不过冲依赖足够低的 AIM_SENSITIVITY。

        Returns:
            float: 目标到屏幕中心的距离（像素）
        """
        dx = target_cx - screen_center_x
        dy = target_cy - screen_center_y
        distance = np.sqrt(dx ** 2 + dy ** 2)

        # 命中范围内即开火（受 shoot() 冷却节流）。Gridshot 靶子密集时高速连射吞吐最高：
        # 实测"每靶只开一枪"的门控会让准星贴着已击杀的靶干等其消失，反而拖慢节奏。
        if distance <= SHOOT_RANGE:
            self.shoot()

        # 始终朝靶心收敛（死区内 aim_at 会自动停止移动）
        self.aim_at(target_cx, target_cy, screen_center_x, screen_center_y)

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
        # 按下时长尽量短：每枪的 sleep 会累加占用主循环时间，过长会拖慢整体节奏
        pydirectinput.mouseDown(button='left')
        time.sleep(0.008)
        pydirectinput.mouseUp(button='left')

        self._last_shot_time = current_time
        self.shots_fired += 1

        return True

    def clear_smoothing(self):
        """清空平滑历史（目标丢失时调用，避免旧偏移值污染下次瞄准）。

        与 reset() 不同，这里不重置射击冷却，避免影响连发节奏。
        """
        self._smooth_history.clear()

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
        }
