import logging
from io import BytesIO

import numpy as np
from PIL import Image

from controllers.websocket_handler import WebSocketHandler, ConnectionState

logger = logging.getLogger(__name__)


class VideoStreamer:
    """
    Handles conversion and transmission of camera frames to a connected WebSocket video client.
    This is typically used for live FPV preview in a custom UI over /video endpoint.
    """

    def __init__(self, ws_handler: WebSocketHandler):
        self.ws_handler = ws_handler

    async def send_camera_frame(self, cam_image_array):
        if self.ws_handler.video_client is None or self.ws_handler.autonomy_connection_state == ConnectionState.DISCONNECTED:
            return
        try:
            cam_image_array = np.uint8(cam_image_array)
            img = Image.fromarray(cam_image_array)
            stream = BytesIO()
            img.save(stream, format='JPEG')
            jpeg_data = stream.getvalue()
            await self.ws_handler.video_client.send(jpeg_data)

        except Exception as e:
            logger.error(f"Error sending camera frame: {e}")