import gc
import math
import time
from multiprocessing import Array, Process
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event as EventClass
from typing import Any

import numpy as np

from metadrive import MetaDriveEnv
from metadrive.component.sensors.base_camera import BaseCamera

from cereal import messaging
# from openpilot.common.numpy_fast import clip  # 不需要這個模組
from openpilot.common.realtime import Ratekeeper
from openpilot.tools.sim.bridge.metadrive.metadrive_common import RGBCameraRoad, RGBCameraWide
from openpilot.tools.sim.lib.camerad import W, H
from openpilot.tools.sim.lib.common import SimulatorState, vec3


def camera_ready():
  return BaseCamera.initialized

def metadrive_vehicle_state(velocity, position, bearing, steering_angle):
  return {
    'velocity': velocity,
    'position': position,
    'bearing': bearing,
    'steering_angle': steering_angle,
  }

def metadrive_simulation_state(running, done, done_info):
  return {
    'running': running,
    'done': done,
    'done_info': done_info,
  }

def get_cam_as_rgb(cam_name):
  cam = BaseCamera.get_camera(cam_name)
  assert cam is not None, f"Camera {cam_name} not found"
  rgb_cam = cam.get_rgb_array_cpu()
  return rgb_cam

def create_array_with_lock(shape, dtype):
  arr = Array('d' if dtype == np.float64 else 'f', int(np.prod(shape)), lock=True)
  arr_np = np.frombuffer(arr.get_obj(), dtype=dtype).reshape(shape)
  return arr, arr_np

def get_current_lane_info(vehicle):
  """Get current lane info to detect out of lane."""
  current_lane = vehicle.lane
  lane_index = vehicle.lane_index
  distance_to_lane_center = vehicle.dist_to_left_side + vehicle.dist_to_right_side
  return lane_index, distance_to_lane_center < 10

def metadrive_process(dual_camera: bool, config: dict, camera_array, wide_camera_array, image_lock,
                      controls_recv: Connection, simulation_state_send: Connection, vehicle_state_send: Connection,
                      exit_event, op_engaged, test_duration, test_run):

  road_image, _ = create_array_with_lock((H, W, 3), np.uint8)
  road_image[:] = 128

  if dual_camera:
    wide_road_image, _ = create_array_with_lock((H, W, 3), np.uint8)
    wide_road_image[:] = 128

  env = MetaDriveEnv(config)

  def reset():
    env.reset()
    return get_current_lane_info(env.vehicle)[0]  # Return initial lane index

  lane_idx_prev = reset()
  start_time = None

  # Hack: ensure BaseCamera.initialized is True, so the cameras are created
  # and we can use them in the main process
  if not camera_ready():
    env.step([0, 0])
    env.engine.force_fps.toggle()

  # send road image
  road_image[...] = get_cam_as_rgb("rgb_road")
  if dual_camera:
    wide_road_image[...] = get_cam_as_rgb("rgb_wide")

  steer_ratio = 4  # 減少轉向比例從 8 到 4，使轉向更靈敏
  vc = [0,0]

  rk = Ratekeeper(100, None)

  while not exit_event.is_set():
    vehicle_state = metadrive_vehicle_state(
      velocity=vec3(x=float(env.vehicle.velocity[0]), y=float(env.vehicle.velocity[1]), z=0),
      position=env.vehicle.position,
      bearing=float(math.degrees(env.vehicle.heading_theta)),
      steering_angle=env.vehicle.steering * env.vehicle.MAX_STEERING
    )
    vehicle_state_send.send(vehicle_state)

    if controls_recv.poll(0):
      while controls_recv.poll(0):
        steer_angle, gas, should_reset = controls_recv.recv()

      # 改善轉向計算 - 更敏感的轉向響應
      steer_metadrive = steer_angle * 1.5 / (env.vehicle.MAX_STEERING * steer_ratio)  # 增加 1.5 倍敏感度
      steer_metadrive = np.clip(steer_metadrive, -1, 1)

      vc = [steer_metadrive, gas]

      if should_reset:
        lane_idx_prev = reset()
        start_time = None

    is_engaged = op_engaged.is_set()
    if is_engaged and start_time is None:
      start_time = time.monotonic()

    if rk.frame % 5 == 0:
      _, _, terminated, _, _ = env.step(vc)
      timeout = True if start_time is not None and time.monotonic() - start_time >= test_duration else False
      lane_idx_curr, on_lane = get_current_lane_info(env.vehicle)
      out_of_lane = lane_idx_curr != lane_idx_prev or not on_lane
      lane_idx_prev = lane_idx_curr

      if terminated or ((out_of_lane or timeout) and test_run):
        if terminated:
          done_result = env.done_function("default_agent")
        elif out_of_lane:
          done_result = (True, {"out_of_lane" : True})
        elif timeout:
          done_result = (True, {"timeout" : True})

        simulation_state = metadrive_simulation_state(
          running=False,
          done=done_result[0],
          done_info=done_result[1],
        )
        simulation_state_send.send(simulation_state)

      if dual_camera:
        wide_road_image[...] = get_cam_as_rgb("rgb_wide")
      road_image[...] = get_cam_as_rgb("rgb_road")
      image_lock.release()

    rk.keep_time()

  env.close()
  del env
  gc.collect()
