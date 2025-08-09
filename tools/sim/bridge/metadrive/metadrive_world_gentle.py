import ctypes
import functools
import multiprocessing
import numpy as np
import time

from multiprocessing import Pipe, Array

from openpilot.tools.sim.bridge.common import QueueMessage, QueueMessageType
from openpilot.tools.sim.bridge.metadrive.metadrive_process_gentle import (metadrive_process, metadrive_simulation_state,
                                                                    metadrive_vehicle_state)
from openpilot.tools.sim.lib.common import SimulatorState, World
from openpilot.tools.sim.lib.camerad import W, H


class MetaDriveWorldGentle(World):
  def __init__(self, status_q, config, test_duration, test_run, dual_camera=False):
    super().__init__(dual_camera)
    self.status_q = status_q
    self.camera_array = Array(ctypes.c_uint8, W*H*3)
    self.road_image = np.frombuffer(self.camera_array.get_obj(), dtype=np.uint8).reshape((H, W, 3))
    self.wide_camera_array = None
    if dual_camera:
      self.wide_camera_array = Array(ctypes.c_uint8, W*H*3)
      self.wide_road_image = np.frombuffer(self.wide_camera_array.get_obj(), dtype=np.uint8).reshape((H, W, 3))

    self.controls_send, self.controls_recv = Pipe()
    self.simulation_state_send, self.simulation_state_recv = Pipe()
    self.vehicle_state_send, self.vehicle_state_recv = Pipe()

    self.exit_event = multiprocessing.Event()
    self.op_engaged = multiprocessing.Event()

    self.image_lock = multiprocessing.Semaphore(value=0)

    config['sensors']['rgb_road'][2]['shared_memory'] = 'SharedMemory'

    self.metadrive_process = multiprocessing.Process(target=metadrive_process, args=(
      dual_camera, config, self.camera_array, self.wide_camera_array, self.image_lock,
      self.controls_recv, self.simulation_state_send, self.vehicle_state_send, self.exit_event, self.op_engaged,
      test_duration, test_run))

    self.metadrive_process.start()

  def read_sensors(self):
    self.image_lock.acquire()

  def read_state(self):
    if self.vehicle_state_recv.poll(0):
      vehicle_state = self.vehicle_state_recv.recv()
      if vehicle_state is not None:
        self.state = SimulatorState()
        self.state.velocity = vehicle_state['velocity']
        self.state.bearing = math.radians(vehicle_state['bearing'])
        self.state.steering_angle = vehicle_state['steering_angle']
        self.state.valid = True

  def read_cameras(self):
    ret = {}

    ret["roadCameraState"] = {
      'image': self.road_image,
      'transform': np.eye(3),
      'width': W,
      'height': H,
    }

    if self.dual_camera:
      ret["wideRoadCameraState"] = {
        'image': self.wide_road_image,
        'transform': np.eye(3),
        'width': W,
        'height': H,
      }

    return ret

  def apply_controls(self, steer_angle, throttle_out, brake_out):
    if self.controls_send.poll() is False:  # the pipe is empty
      should_reset = False
      # Check if we should reset based on message in status queue
      while not self.status_q.empty():
        msg = self.status_q.get()
        if msg.msg_type == QueueMessageType.RESET_SIMULATION:
          should_reset = True

      self.controls_send.send((steer_angle, throttle_out, should_reset))

  def engage_openpilot(self):
    self.op_engaged.set()

  def disengage_openpilot(self):
    self.op_engaged.clear()

  def simulation_state(self):
    if self.simulation_state_recv.poll(0):
      state = self.simulation_state_recv.recv()
      if state is not None:
        return state
    return metadrive_simulation_state(running=True, done=False, done_info={})

  def close(self):
    self.exit_event.set()
    self.metadrive_process.join()

  def reset(self):
    """Reset the simulation"""
    pass

  def tick(self):
    """Update simulation state"""
    self.read_state()

import math
