# Aim Lab 自动瞄准射击程序 🎯

基于计算机视觉的 Aim Lab 自动瞄准射击辅助工具。

## 技术栈

| 模块 | 技术 |
|------|------|
| 屏幕捕获 | DXcam (DirectX) |
| 目标检测 | OpenCV HSV 颜色过滤 |
| 鼠标控制 | PyDirectInput |
| 热键监听 | keyboard |

## 环境要求

- Python 3.12+
- Conda 环境 `aimlab`（已配置好所有依赖）

## 快速开始

```bash
conda activate aimlab
cd aim_bot
python main.py
```

## 操作说明

| 按键 | 功能 |
|------|------|
| **F6** | 开启 / 关闭 自动瞄准 |
| **F8** | 退出程序 |

## 配置参数

所有参数在 `aim_bot/config.py` 中调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `AIM_SENSITIVITY` | 1.0 | 瞄准灵敏度 (0.5~1.5) |
| `AIM_SMOOTHING` | 3 | 瞄准平滑度 |
| `AIM_DEADZONE` | 15px | 瞄准死区 |
| `SHOOT_RANGE` | 40px | 自动射击范围 |
| `SHOOT_COOLDOWN` | 0.15s | 射击冷却时间 |
| `DETECT_RADIUS` | 200px | 检测区域半径 |
| `AUTO_SHOOT` | True | 自动射击开关 |
| `SHOW_DEBUG` | False | 调试窗口开关 |
| `TOGGLE_KEY` | F6 | 开关热键 |
| `EXIT_KEY` | F8 | 退出热键 |

检测颜色也可在 `TARGET_COLORS` 中配置（支持橙色、绿色、红色、蓝色）。

## 项目结构

```
├── aim_bot/
│   ├── config.py          # 配置文件
│   ├── screen_capture.py  # 屏幕捕获
│   ├── detector.py        # 目标检测
│   ├── aim_assist.py      # 瞄准与射击
│   └── main.py            # 主程序入口
└── README.md
```

## 工作原理

1. DXcam 实时捕获屏幕画面
2. OpenCV 将画面转为 HSV 颜色空间
3. 通过颜色过滤识别靶标位置
4. 计算靶标与屏幕中心的偏移量
5. 平滑移动鼠标至目标
6. 准星进入射击范围后自动开火
