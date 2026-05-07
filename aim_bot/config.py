"""
Aim Lab 自动瞄准射击程序 - 配置文件
所有可调节参数集中管理
"""

import numpy as np

# ============ 窗口设置 ============
# Aim Lab 窗口标题（用于自动定位）
WINDOW_TITLE = "Aim Lab"

# ============ 目标检测颜色范围 (HSV) ============
# HSV 颜色模型: H(色相 0-180), S(饱和度 0-255), V(明度 0-255)
# Aim Lab 常见靶标颜色
# 橙色/黄色靶心 —— Aim Lab 最常用的靶心颜色
TARGET_ORANGE_LOWER = np.array([5, 150, 150])   # H≈5° 偏红橙
TARGET_ORANGE_UPPER = np.array([25, 255, 255])  # H≈25° 偏黄橙

# 绿色靶标
TARGET_GREEN_LOWER = np.array([40, 100, 100])   # H≈40° 黄绿
TARGET_GREEN_UPPER = np.array([80, 255, 255])   # H≈80° 青绿

# 红色靶标（红色在 HSV 中跨越 0° 边界，需要两个范围）
TARGET_RED_LOWER1 = np.array([0, 150, 150])     # 红色范围1: H 0-10°
TARGET_RED_UPPER1 = np.array([10, 255, 255])
TARGET_RED_LOWER2 = np.array([170, 150, 150])   # 红色范围2: H 170-180°
TARGET_RED_UPPER2 = np.array([180, 255, 255])

# 蓝色靶标
TARGET_BLUE_LOWER = np.array([100, 100, 100])   # H≈100° 蓝绿
TARGET_BLUE_UPPER = np.array([130, 255, 255])   # H≈130° 蓝色

# 要检测的颜色组合（可自由组合）
# 默认只检测橙色（最常见靶心颜色）
# 如需检测多种颜色，取消对应行的注释即可
TARGET_COLORS = [
    ("orange", TARGET_ORANGE_LOWER, TARGET_ORANGE_UPPER),
    # ("green", TARGET_GREEN_LOWER, TARGET_GREEN_UPPER),
    # ("red1", TARGET_RED_LOWER1, TARGET_RED_UPPER1),
    # ("red2", TARGET_RED_LOWER2, TARGET_RED_UPPER2),
    # ("blue", TARGET_BLUE_LOWER, TARGET_BLUE_UPPER),
]

# ============ 瞄准设置 ============
# 瞄准灵敏度 (鼠标移动速度倍数)
# 值越大，鼠标移动越快；建议 0.5 ~ 1.5
AIM_SENSITIVITY = 1.0

# 瞄准平滑度 (帧数，值越大越平滑但反应越慢)
# 使用移动平均平滑鼠标移动
AIM_SMOOTHING = 3

# 瞄准死区 (像素) - 目标离屏幕中心小于此值时不移动鼠标
AIM_DEADZONE = 15

# ============ 射击设置 ============
# 自动射击触发范围 (像素) - 准星距离目标中心多远时自动开枪
SHOOT_RANGE = 40

# 射击后冷却时间 (秒) - 防止连发过快
SHOOT_COOLDOWN = 0.15

# 是否启用自动射击
AUTO_SHOOT = True

# ============ 检测区域设置 ============
# 屏幕中心检测区域的半径 (像素)
# 只检测屏幕中心这个范围内的目标，提高性能
DETECT_RADIUS = 200

# 检测帧率 (每隔多少帧执行一次完整检测)
# 1 = 每帧都检测，2 = 隔一帧检测一次... 用于性能优化
DETECT_FRAME_SKIP = 1

# ============ 显示/调试设置 ============
# 是否显示调试窗口 (显示检测到的目标和瞄准信息)
SHOW_DEBUG = False

# ============ 热键设置 ============
# 启动/停止自动瞄准的热键
TOGGLE_KEY = "F6"

# 退出程序的热键
EXIT_KEY = "F8"
