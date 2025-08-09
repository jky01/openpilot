
import os
import time
from multiprocessing import Queue

# 強制 GPU 設置
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

from openpilot.tools.sim.bridge.metadrive.metadrive_bridge import MetaDriveBridge

def create_minimal_bridge():
    """創建最小化橋接器"""
    queue = Queue()
    
    # 使用最低配置
    bridge = MetaDriveBridge(
        dual_camera=False,  # 單攝像頭
        high_quality=False, # 低質量模式
        test_duration=float('inf'),
        test_run=False
    )
    
    print("🎮 啟動最小化模擬器...")
    process = bridge.run(queue)
    
    return queue, process, bridge

if __name__ == "__main__":
    queue, process, bridge = create_minimal_bridge()
    
    try:
        print("⌨️  鍵盤控制：2=啟動, 1=加速, 3=減速, S=煞車, Q=退出")
        from openpilot.tools.sim.lib.keyboard_ctrl import keyboard_poll_thread
        keyboard_poll_thread(queue)
    except KeyboardInterrupt:
        print("\n🛑 關閉模擬器...")
    finally:
        bridge.shutdown()
        process.join()
