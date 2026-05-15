# Aim Lab 自动瞄准射击程序

基于计算机视觉的 Aim Lab 自动瞄准射击辅助工具。项目仅面向 Windows，因为屏幕捕获和输入控制依赖 DirectX、Win32 API 和 PyDirectInput。

## 技术栈

| 模块 | 技术 |
|------|------|
| 屏幕捕获 | DXcam (DirectX) |
| 目标检测 | OpenCV HSV 颜色过滤 |
| 鼠标控制 | PyDirectInput |
| 热键监听 | keyboard |

## 环境要求

- Windows 10/11
- Python 3.12+
- Aim Lab 建议使用窗口化或无边框窗口模式，便于程序定位游戏客户区
- 如热键监听或鼠标控制无效，请使用管理员权限启动终端

## 快速开始

```bash
conda activate aimlab
pip install -r requirements.txt
python -m aim_bot.main
```

也可以直接运行入口文件：

```bash
python aim_bot/main.py
```

## 操作说明

| 按键 | 功能 |
|------|------|
| **F6** | 开启 / 关闭自动瞄准 |
| **F8** | 退出程序 |

## 配置参数

所有参数在 `aim_bot/config.py` 中调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `AIM_SENSITIVITY` | 1.0 | 瞄准灵敏度，建议 0.5 到 1.5 |
| `AIM_SMOOTHING` | 3 | 瞄准平滑度 |
| `AIM_DEADZONE` | 15px | 瞄准死区 |
| `SHOOT_RANGE` | 40px | 自动射击触发范围 |
| `SHOOT_COOLDOWN` | 0.15s | 射击冷却时间 |
| `DETECT_RADIUS` | 200px | 检测区域半径 |
| `AUTO_SHOOT` | True | 自动射击开关 |
| `SHOW_DEBUG` | False | 调试窗口开关 |
| `TOGGLE_KEY` | F6 | 开关热键 |
| `EXIT_KEY` | F8 | 退出热键 |

检测颜色可在 `TARGET_COLORS` 中配置，默认只检测橙色，也可启用绿色、红色或蓝色范围。

## 项目结构

```text
aim_bot/
  config.py          # 配置文件
  screen_capture.py  # 屏幕捕获
  detector.py        # 目标检测
  aim_assist.py      # 瞄准与射击
  main.py            # 主程序入口
requirements.txt
README.md
```

## 工作原理

1. DXcam 实时捕获 Aim Lab 窗口或全屏画面
2. OpenCV 将画面转换到 HSV 颜色空间
3. 通过颜色过滤识别目标位置
4. 计算目标与画面中心的偏移量
5. 平滑移动鼠标到目标方向
6. 准星进入射击范围后自动开火
