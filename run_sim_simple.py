#!/usr/bin/env python3
"""
簡化版 openpilot 模擬器
專注於核心優化，不依賴額外套件
"""

import os
import argparse
from typing import Any
from multiprocessing import Queue

def setup_basic_optimization():
    """設置基礎優化環境變數"""
    print("🔧 設置基礎優化環境...")

    # GPU 相關優化
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['__GL_SYNC_TO_VBLANK'] = '0'
    os.environ['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'

    # 性能優化
    os.environ['OMP_NUM_THREADS'] = '6'  # 使用一半 CPU 核心
    os.environ['OPENBLAS_NUM_THREADS'] = '6'

    # 禁用不必要的功能來提升性能
    os.environ['BLOCK'] = 'camerad,loggerd,encoderd,micd,logmessaged,sensord'

    print("✅ 基礎優化設置完成")

def create_simple_bridge(dual_camera=False, high_quality=False):
    """創建簡化的模擬器橋接器"""
    setup_basic_optimization()

    from openpilot.tools.sim.bridge.metadrive.metadrive_bridge import MetaDriveBridge

    queue: Any = Queue()

    print("🚗 正在初始化簡化模擬器...")
    # 使用單攝像頭和低質量模式來提升性能
    simulator_bridge = MetaDriveBridge(dual_camera, high_quality)
    print("✅ 啟動模擬器進程...")
    simulator_process = simulator_bridge.run(queue)

    return queue, simulator_process, simulator_bridge

def main():
    parser = argparse.ArgumentParser(description='簡化的 openpilot 模擬器')
    parser.add_argument('--dual_camera', action='store_true', help='使用雙攝像頭（影響性能）')
    parser.add_argument('--high_quality', action='store_true', help='高質量模式（影響性能）')
    args = parser.parse_args()

    print("🚀 啟動簡化版 openpilot 模擬測試")
    print("=" * 50)
    print("⚡ 優化設置：")
    print(f"  • 雙攝像頭：{'開啟' if args.dual_camera else '關閉（性能優先）'}")
    print(f"  • 高質量：{'開啟' if args.high_quality else '關閉（性能優先）'}")
    print("  • 減少後台進程")
    print("  • GPU 加速啟用")
    print("📋 控制說明：")
    print("  2 - 啟動巡航控制")
    print("  1 - 加速 | 2 - 減速 | 3 - 取消")
    print("  S - 煞車 | Q - 退出 | R - 重置")
    print("=" * 50)

    # 使用簡化配置啟動
    queue, simulator_process, simulator_bridge = create_simple_bridge(
        dual_camera=args.dual_camera,
        high_quality=args.high_quality
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
