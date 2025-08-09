#!/usr/bin/env python3
"""
GPU 優化的 openpilot 模擬器
專門優化 GPU 利用率和性能
"""

import os
import sys
from typing import Any
from multiprocessing import Queue

def setup_gpu_environment():
    """設置 GPU 優化環境"""
    print("🔧 設置 GPU 優化環境...")

    # 強制使用 NVIDIA GPU
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['__NV_PRIME_RENDER_OFFLOAD'] = '1'
    os.environ['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'

    # 關閉垂直同步以提高性能
    os.environ['__GL_SYNC_TO_VBLANK'] = '0'
    os.environ['__GL_YIELD'] = 'NOTHING'

    # CUDA 優化
    os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
    os.environ['CUDA_CACHE_DISABLE'] = '0'

    # MetaDrive GPU 優化
    os.environ['PANDA3D_USE_OPENGL_ES'] = '0'
    os.environ['PANDA3D_PREFER_OPENGL_1'] = '0'

    # 性能優化
    os.environ['OMP_NUM_THREADS'] = '4'
    os.environ['OPENBLAS_NUM_THREADS'] = '4'
    os.environ['MKL_NUM_THREADS'] = '4'

    print("✅ GPU 環境設置完成")

def patch_metadrive_for_gpu():
    """修改 MetaDrive 配置以優化 GPU 使用"""
    print("🔧 應用 GPU 優化補丁...")

    import openpilot.tools.sim.bridge.metadrive.metadrive_bridge as bridge_module

    # 保存原始函數
    original_spawn_world = bridge_module.MetaDriveBridge.spawn_world
    original_create_map = bridge_module.create_map

    def optimized_create_map(track_size=60):
        """優化的地圖配置"""
        curve_len = track_size * 2
        return {
            'type': bridge_module.MapGenerateMethod.PG_MAP_FILE,
            'lane_num': 2,
            'lane_width': 4.5,
            'config': [
                None,
                bridge_module.straight_block(track_size * 2),  # 更長直道
                bridge_module.curve_block(curve_len, 60),      # 較緩彎道
                bridge_module.straight_block(track_size),
                bridge_module.curve_block(curve_len, 60),
                bridge_module.straight_block(track_size),
                bridge_module.curve_block(curve_len, 60),
                bridge_module.straight_block(track_size),
                bridge_module.curve_block(curve_len, 60),
            ]
        }

    def optimized_spawn_world(self, queue):
        """GPU 優化的世界生成"""
        from openpilot.tools.sim.lib.camerad import W, H
        from openpilot.tools.sim.bridge.metadrive.metadrive_common import RGBCameraRoad, RGBCameraWide
        from openpilot.tools.sim.bridge.metadrive.metadrive_world import MetaDriveWorld
        from metadrive.component.sensors.base_camera import _cuda_enable

        sensors = {
            "rgb_road": (RGBCameraRoad, W, H)
        }

        if self.dual_camera:
            sensors["rgb_wide"] = (RGBCameraWide, W, H)

        config = {
            'use_render': False,  # 關閉渲染以提升性能
            'vehicle_config': {
                'enable_reverse': False,
                'render_vehicle': False,
                'image_source': "rgb_road",
            },
            'sensors': sensors,
            'image_on_cuda': True,  # 強制啟用 CUDA
            'image_observation': True,
            'interface_panel': [],
            'out_of_route_done': False,
            'on_continuous_line_done': False,
            'crash_vehicle_done': False,
            'crash_object_done': False,
            'arrive_dest_done': False,
            'traffic_density': 0.0,  # 移除交通以提升性能
            'map_config': optimized_create_map(),
            'decision_repeat': 1,
            'physics_world_step_size': self.TICKS_PER_FRAME/100,
            'preload_models': True,   # 預載模型
            'show_logo': False,
            'anisotropic_filtering': False,
            # GPU 性能優化
            'multi_thread': False,   # 單線程避免競爭
            'use_chase_camera_follow_lane': False,
            'global_light': False,   # 關閉全局光照
            'headless_image_on_cuda': True,  # CUDA 圖像處理
        }

        return MetaDriveWorld(queue, config, self.test_duration, self.test_run, self.dual_camera)

    # 應用補丁
    bridge_module.MetaDriveBridge.spawn_world = optimized_spawn_world
    bridge_module.create_map = optimized_create_map

    print("✅ GPU 優化補丁已應用")
    return original_spawn_world, original_create_map

def create_gpu_optimized_bridge(dual_camera=True, high_quality=False):
    """創建 GPU 優化的模擬器橋接器"""
    # 設置環境
    setup_gpu_environment()

    # 應用補丁
    original_spawn_world, original_create_map = patch_metadrive_for_gpu()

    try:
        from openpilot.tools.sim.bridge.metadrive.metadrive_bridge import MetaDriveBridge

        queue: Any = Queue()

        print("🚗 正在初始化 GPU 優化的 MetaDrive 模擬器...")
        simulator_bridge = MetaDriveBridge(dual_camera, high_quality)
        print("✅ 啟動模擬器進程...")
        simulator_process = simulator_bridge.run(queue)

        return queue, simulator_process, simulator_bridge

    except Exception as e:
        # 如果失敗，恢復原始函數
        import openpilot.tools.sim.bridge.metadrive.metadrive_bridge as bridge_module
        bridge_module.MetaDriveBridge.spawn_world = original_spawn_world
        bridge_module.create_map = original_create_map
        raise e

def main():
    print("🚀 啟動 GPU 優化的 openpilot 模擬測試")
    print("=" * 60)
    print("⚡ GPU 優化設置：")
    print("  • 強制 CUDA 加速")
    print("  • 關閉垂直同步")
    print("  • 優化渲染管線")
    print("  • 移除交通密度")
    print("  • 預載模型")
    print("  • 單線程處理")
    print("📋 控制說明：")
    print("  2 - 啟動巡航控制")
    print("  1 - 加速 | 2 - 減速 | 3 - 取消")
    print("  S - 煞車 | Q - 退出 | R - 重置")
    print("=" * 60)

    # 檢查 GPU 狀態
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA 可用: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️  CUDA 不可用，性能可能受限")
    except ImportError:
        print("⚠️  PyTorch 未安裝，無法檢查 CUDA")

    # 使用 GPU 優化配置啟動
    queue, simulator_process, simulator_bridge = create_gpu_optimized_bridge(
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
