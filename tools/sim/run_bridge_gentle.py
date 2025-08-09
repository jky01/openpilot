#!/usr/bin/env python3

import argparse
import os
from typing import Any
from multiprocessing import Queue

# 優化轉向性能的環境變數
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
os.environ.setdefault('__GL_SYNC_TO_VBLANK', '0')

from openpilot.tools.sim.bridge.metadrive.metadrive_bridge_gentle import MetaDriveBridgeGentle

def create_gentle_bridge(dual_camera=True, high_quality=False):
  """創建帶有緩和轉彎的模擬器橋接器"""
  queue: Any = Queue()

  print("🚗 正在初始化緩和轉彎的 MetaDrive 模擬器...")
  simulator_bridge = MetaDriveBridgeGentle(dual_camera, high_quality)
  print("✅ 啟動模擬器進程...")
  simulator_process = simulator_bridge.run(queue)

  return queue, simulator_process, simulator_bridge

def main():
  print("🛣️  啟動緩和轉彎的 openpilot 模擬測試")
  print("=" * 50)
  print("📋 控制說明：")
  print("  2 - 啟動巡航控制")
  print("  1 - 加速")
  print("  2 - 減速")
  print("  3 - 取消巡航")
  print("  S - 煞車")
  print("  Q - 退出")
  print("  R - 重置")
  print("🔧 優化設置：")
  print("  • 轉彎角度：從 90° 減少到 45°")
  print("  • 轉彎半徑：增加 2 倍")
  print("  • 車道寬度：增加到 5.0m")
  print("  • 直道長度：延長 2 倍")
  print("=" * 50)

  # 使用緩和的轉彎配置啟動
  queue, simulator_process, simulator_bridge = create_gentle_bridge(
    dual_camera=True,
    high_quality=False  # 使用低質量模式提升性能
  )

  try:
    # 啟動鍵盤控制
    from openpilot.tools.sim.lib.keyboard_ctrl import keyboard_poll_thread
    keyboard_poll_thread(queue)
  except KeyboardInterrupt:
    print("\n🛑 正在關閉模擬器...")
  finally:
    simulator_bridge.shutdown()
    simulator_process.join()
    print("✅ 模擬器已關閉")

if __name__ == "__main__":
  main()
