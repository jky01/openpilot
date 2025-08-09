#!/usr/bin/env python3
"""
緩和轉彎的 openpilot 模擬器啟動器
修改原始參數以改善轉彎性能
"""

import argparse
import os
import tempfile
from typing import Any
from multiprocessing import Queue

# 設置性能環境變數
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
os.environ.setdefault('__GL_SYNC_TO_VBLANK', '0')

def patch_metadrive_bridge():
    """暫時修改 MetaDrive 橋接器以改善轉彎"""
    import openpilot.tools.sim.bridge.metadrive.metadrive_bridge as bridge_module
    import openpilot.tools.sim.bridge.metadrive.metadrive_process as process_module

    # 保存原始函數
    original_create_map = bridge_module.create_map
    original_metadrive_process = process_module.metadrive_process

    def create_gentle_map(track_size=80):
        """創建更緩和的地圖"""
        curve_len = track_size * 3  # 增加彎道長度
        return {
            'type': bridge_module.MapGenerateMethod.PG_MAP_FILE,
            'lane_num': 2,
            'lane_width': 5.0,  # 增加車道寬度
            'config': [
                None,
                bridge_module.straight_block(track_size * 2),  # 更長的直道
                bridge_module.curve_block(curve_len, 30),      # 減少轉彎角度到 30 度
                bridge_module.straight_block(track_size),
                bridge_module.curve_block(curve_len, 30),
                bridge_module.straight_block(track_size),
                bridge_module.curve_block(curve_len, 30),
                bridge_module.straight_block(track_size),
                bridge_module.curve_block(curve_len, 30),
            ]
        }

    # 修補函數
    bridge_module.create_map = create_gentle_map

    print("🔧 已應用緩和轉彎補丁")
    return original_create_map

def create_bridge(dual_camera=True, high_quality=False):
    """創建模擬器橋接器"""
    # 先應用補丁
    original_create_map = patch_metadrive_bridge()

    try:
        from openpilot.tools.sim.bridge.metadrive.metadrive_bridge import MetaDriveBridge

        queue: Any = Queue()

        print("🚗 正在初始化緩和轉彎的 MetaDrive 模擬器...")
        simulator_bridge = MetaDriveBridge(dual_camera, high_quality)
        print("✅ 啟動模擬器進程...")
        simulator_process = simulator_bridge.run(queue)

        return queue, simulator_process, simulator_bridge

    except Exception as e:
        # 如果失敗，恢復原始函數
        import openpilot.tools.sim.bridge.metadrive.metadrive_bridge as bridge_module
        bridge_module.create_map = original_create_map
        raise e

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
    print("  • 轉彎角度：從 90° 減少到 30°")
    print("  • 轉彎半徑：增加 3 倍")
    print("  • 車道寬度：增加到 5.0m")
    print("  • 直道長度：延長 2 倍")
    print("=" * 50)

    # 使用緩和的轉彎配置啟動
    queue, simulator_process, simulator_bridge = create_bridge(
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
