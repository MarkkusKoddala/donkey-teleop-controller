import time
from enum import Enum

import cv2
from cv2 import aruco

from services.experiment_logger import ExperimentLogger


def _current_time_ms():
    return time.time_ns() // 1_000_000


class ControlSource(Enum):
    USER = "user"
    AUTONOMOUS = "local_angle"


class TeleopDecisionManager:
    def __init__(self, timeout_ms=400):
        self.current_source = ControlSource.USER

        self.throttle = 0.0
        self.angle = 0.0

        self.timeout_ms = timeout_ms
        self.last_user_input_time_ms = _current_time_ms()

        self.autonomy_enabled = False
        self.recording_enabled = False

        self.last_decided_control_source = None

        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_100)
        self.aruco_params = aruco.DetectorParameters_create()

    def update_user_input(self, throttle, angle):
        self.throttle = throttle
        self.angle = angle
        self.last_user_input_time_ms = _current_time_ms()

    def reset_controls(self):
        self.throttle = 0.0
        self.angle = 0.0

    def has_timed_out(self):
        return _current_time_ms() - self.last_user_input_time_ms > self.timeout_ms

    def set_control_source(self, state: ControlSource):
        if self.current_source != state:
            self.current_source = state

    def select_active_source(self):
        """
        Selects the active control source based on system state.

        - If autonomy is disabled, always use USER control.
        - If autonomy is enabled:
            * If the current source is already AUTONOMOUS, keep it.
            * Otherwise, default to USER control.
        """


        if not self.autonomy_enabled:
            return ControlSource.AUTONOMOUS

        if self.current_source == ControlSource.AUTONOMOUS:
            return ControlSource.AUTONOMOUS

        return ControlSource.USER

    def get_active_control(self, cam_image_array):
        """
        Returns a tuple (angle, throttle, mode, isRecording) based on the current control logic.
        - If USER control is active, it returns the user inputs (resetting them if they timed out).
        - If AUTONOMOUS control is active, it returns default values for AI control.
        """
        decided_source = self.select_active_source()

        if decided_source == ControlSource.USER:
            if self.has_timed_out():
                self.reset_controls()
            return self.angle, self.throttle, decided_source.value, self.recording_enabled

        throttle = self.evaluate_aruco_signals(cam_image_array)

        return 0.0, throttle, decided_source.value, False

    def evaluate_aruco_signals(self, cam_image_array):
        gray = cv2.cvtColor(cam_image_array, cv2.COLOR_RGB2GRAY)
        corners, ids, _ = aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)

        if ids is not None and len(ids) > 0:
            print(f"Found {len(ids)} ArUco markers.")
            return 0.0

        return 0.9
