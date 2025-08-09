#!/usr/bin/env python3

import argparse
import os
from typing import Any
from multiprocessing import Queue

# 設置性能優化環境變數
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['__GL_SYNC_TO_VBLANK'] = '0'

from openpilot.tools.sim.bridge.metadrive.metadrive_bridge import MetaDriveBridge

def create_bridge(dual_camera=True, high_quality=False):
  """創建優化的模擬器橋接器"""
  queue: Any = Queue()

  print("正在初始化 MetaDrive 模擬器...")
  simulator_bridge = MetaDriveBridge(dual_camera, high_quality)
  print("啟動模擬器進程...")
  simulator_process = simulator_bridge.run(queue)

  return queue, simulator_process, simulator_bridge

def main():
  print("🚗 啟動優化的 openpilot 模擬測試")
  print("控制說明：")
  print("  2 - 啟動巡航控制")
  print("  1 - 加速")
  print("  2 - 減速")
  print("  3 - 取消巡航")
  print("  S - 煞車")
  print("  Q - 退出")
  print("  R - 重置")
  print("-" * 40)

  # 使用優化參數啟動
  queue, simulator_process, simulator_bridge = create_bridge(
    dual_camera=True,
    high_quality=False  # 使用低質量模式提升性能
  )

  try:
    # 啟動鍵盤控制
    from openpilot.tools.sim.lib.keyboard_ctrl import keyboard_poll_thread
    keyboard_poll_thread(queue)
  except KeyboardInterrupt:
    print("\n正在關閉模擬器...")
  finally:
    simulator_bridge.shutdown()
    simulator_process.join()
    print("模擬器已關閉")

if __name__ == "__main__":
  main()
