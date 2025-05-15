import asyncio
import threading

import aiohttp_cors
import cv2
from aiohttp import web

from controllers.control_api_handler import ControlAPIHandler
from controllers.websocket_handler import WebSocketHandler, logger
from core.teleop_decision_manager import TeleopDecisionManager
from services.experiment_logger import ExperimentLogger
from services.resource_monitor import ResourceMonitor
from services.video_streamer import VideoStreamer


def run(cam_image_array=None):
    """
    If 'threaded=False' in DonkeyCar config, this method is called.
    But we typically set 'threaded=True' and use run_threaded below.
    """
    return 0.0, 0.0, "user"


class TeleopControlPart:
    """
    Central orchestrator for DonkeyCar teleoperation.

    - Manages control flow and input/output pipelines.
    - Runs WebSocket and HTTP servers in an asyncio event loop.
    - Interfaces with camera input and decision logic via CarControlManager.
    - Provides real-time video streaming, control toggling, and telemetry updates.
    """

    def __init__(self, cfg):
        #warnings.filterwarnings("ignore", category=PicameraDeprecated)

        self.config = cfg

        # Set up a dedicated asyncio loop for async tasks
        self.loop = asyncio.new_event_loop()
        self._start_event_loop_in_thread()

        self.teleop_decision_manager = TeleopDecisionManager()

        self.ws_handler = WebSocketHandler(self.loop, self.teleop_decision_manager)
        self.http_handler = ControlAPIHandler(self)
        self.http_handler.start()


        self.video_streamer = VideoStreamer(self.ws_handler)

        # Tracks the last submitted streaming task (to allow cancellation)
        self._last_stream_task = None

        # Optional: system resource monitoring and experiment logging
        #self.logger = ExperimentLogger()
        #self.resource_monitor = ResourceMonitor(self.logger)
        #self.resource_monitor.start()

    def _start_event_loop_in_thread(self) -> None:
        thread = threading.Thread(target=self._start_event_loop, daemon=True)
        thread.start()

    def _start_event_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_threaded(self, cam_image_array):

        resized_cam_image_array = None
        if cam_image_array is not None:
            self._run_async_task(self.video_streamer.send_camera_frame(cam_image_array))
            resized_cam_image_array = cv2.resize(cam_image_array, (160, 120))

        # False at the end is about whether to record or no
        angle, throttle, mode, recording = self.teleop_decision_manager.get_active_control(cam_image_array)
        return angle, throttle, mode, recording, resized_cam_image_array

    def _run_async_task(self, coroutine):
        # Submit coroutine to async event loop; cancel the previous one if still pending
        if not self.loop.is_running():
            logger.error("Event loop is not running!")
            return
        try:
            if self._last_stream_task and not self._last_stream_task.done():
                self._last_stream_task.cancel()

            self._last_stream_task = asyncio.run_coroutine_threadsafe(coroutine, self.loop)

        except Exception as e:
            logger.error(f"Error running async task: {e}")

    def update(self, mode=None):
        # Optional: DonkeyCar calls this once per loop if defined (not used here)
        pass

    def set_tub(self, tub):
        # Optional: DonkeyCar calls this to provide access to Tub recorder (not used here)
        pass
