#!/usr/bin/env python3
"""
最小化 openpilot 模擬器 - 強制 GPU 加速
專為 RTX 2070 優化
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

def setup_gpu_environment():
    """設置強制 GPU 加速環境"""
    print("🚀 設置 RTX 2070 GPU 加速環境...")

    # 強制使用 GPU 0
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['__NV_PRIME_RENDER_OFFLOAD'] = '1'
    os.environ['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
    os.environ['__GL_SYNC_TO_VBLANK'] = '0'

    # 強制 OpenGL 使用 NVIDIA
    os.environ['VK_ICD_FILENAMES'] = '/usr/share/vulkan/icd.d/nvidia_icd.json'

    # 性能優化
    os.environ['OMP_NUM_THREADS'] = '4'
    os.environ['OPENBLAS_NUM_THREADS'] = '4'

    print("✅ GPU 環境設置完成")

def setup_minimal_openpilot():
    """設置最小化 openpilot 環境"""
    print("🔧 設置最小化 openpilot...")

    # 基本模擬環境
    os.environ['PASSIVE'] = '0'
    os.environ['NOBOARD'] = '1'
    os.environ['SIMULATION'] = '1'
    os.environ['SKIP_FW_QUERY'] = '1'
    os.environ['FINGERPRINT'] = 'HONDA_CIVIC_2022'

    # 禁用所有非必需組件來減輕負載
    os.environ['BLOCK'] = 'camerad,loggerd,encoderd,micd,logmessaged,sensord,updated,athena,proclogd'

    # 禁用日誌輸出來提升性能
    os.environ['PYTHONUNBUFFERED'] = '0'

    print("✅ 最小化配置完成")

def kill_existing_processes():
    """徹底清理現有進程"""
    print("🧹 清理現有進程...")

    commands = [
        "pkill -f manager.py",
        "pkill -f run_bridge",
        "pkill -f metadrive",
        "pkill -f openpilot"
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd.split(), capture_output=True)
        except:
            pass

    time.sleep(2)
    print("✅ 進程清理完成")

def launch_minimal_openpilot():
    """啟動最小化 openpilot"""
    print("🎯 啟動最小化 openpilot...")

    openpilot_cmd = [
        'bash', '-c',
        'source openpilot_venv/bin/activate && cd system/manager && python3 manager.py'
    ]

    return subprocess.Popen(openpilot_cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          preexec_fn=os.setsid)

def create_minimal_bridge_script():
    """創建最小化橋接腳本"""
    bridge_code = '''
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
        print("\\n🛑 關閉模擬器...")
    finally:
        bridge.shutdown()
        process.join()
'''

    with open('/home/aa/repo/openpilot/minimal_bridge.py', 'w') as f:
        f.write(bridge_code)

    os.chmod('/home/aa/repo/openpilot/minimal_bridge.py', 0o755)
    print("✅ 最小化橋接腳本創建完成")

def main():
    print("🚀 最小化 openpilot RTX 2070 模擬器啟動")
    print("=" * 60)

    try:
        # 1. 清理現有進程
        kill_existing_processes()

        # 2. 設置環境
        setup_gpu_environment()
        setup_minimal_openpilot()

        # 3. 創建橋接腳本
        create_minimal_bridge_script()

        # 4. 啟動 openpilot
        print("🎯 啟動 openpilot（背景執行）...")
        openpilot_process = launch_minimal_openpilot()

        # 5. 等待 openpilot 啟動
        print("⏳ 等待 openpilot 啟動（15秒）...")
        time.sleep(15)

        # 6. 啟動橋接器
        print("🌉 啟動最小化橋接器...")
        bridge_cmd = [
            'bash', '-c',
            'source openpilot_venv/bin/activate && python3 minimal_bridge.py'
        ]

        subprocess.run(bridge_cmd)

    except KeyboardInterrupt:
        print("\n🛑 正在關閉...")
    finally:
        # 清理
        kill_existing_processes()
        print("✅ 清理完成")

if __name__ == "__main__":
    main()
