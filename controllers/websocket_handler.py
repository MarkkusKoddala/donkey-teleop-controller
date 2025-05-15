import asyncio
import json
import logging
from enum import Enum
import subprocess
import re
import websockets
from websockets.server import serve

from core.teleop_decision_manager import TeleopDecisionManager, ControlSource

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class ConnectionState(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


def get_wifi_details(interface="wlan0"):
    """
    Retrieves the current connected BSSID and signal strength using `iw`.
    Returns a dictionary with 'ap_mac' and 'signal_strength'.
    """
    details = {"ap_mac": None, "signal_strength": None}

    try:
        result = subprocess.run(
            ["iw", "dev", interface, "link"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        output = result.stdout

        # Extract BSSID (AP MAC)
        bssid_match = re.search(r"Connected to ([\da-fA-F:]{17})", output)
        if bssid_match:
            details["ap_mac"] = bssid_match.group(1)

        # Extract signal strength (RSSI)
        signal_match = re.search(r"signal: (-\d+)", output)
        if signal_match:
            details["signal_strength"] = float(signal_match.group(1))

    except subprocess.CalledProcessError as e:
        logger.error(f"`iw` command failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while reading Wi-Fi info: {e}")

    return details


class WebSocketHandler:
    def __init__(self, loop: asyncio.AbstractEventLoop, teleop_decisin_manager: TeleopDecisionManager,
                 host="0.0.0.0", port=8080):
        self.host = host
        self.port = port

        self.autonomy_connection_state = ConnectionState.DISCONNECTED

        self.teleop_decisin_manager = teleop_decisin_manager
        self.control_client = None
        self.video_client = None
        self.telemetry_client = None
        self.autonomy_client = None

        self.loop = loop
        # Start dedicated WebRTC client in a thread-safe manner.
        asyncio.run_coroutine_threadsafe(self.start_server(), self.loop)

        self.counter = 0

    async def start_server(self):
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        try:
            server = await serve(self.router, self.host, self.port)
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            await server.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")

    async def router(self, websocket, path):
        if path == "/control":
            await self.control_handler(websocket)
        elif path == "/video":
            await self.video_handler(websocket)
        elif path == "/telemetry":
            await self.telemetry_handler(websocket)
        elif path == "/autonomy":
            await self.autonomy_handler(websocket)
        else:
            await websocket.close(code=1003, reason="Unknown path")

    async def control_handler(self, websocket):
        self.control_client = websocket
        logger.info(f"Control client connected: {websocket.remote_address}")
        try:
            while True:
                try:
                    message = await websocket.recv()
                    await self._on_control_message(websocket, message)

                except Exception as e:
                    logger.error(f"Error handling control connection: {e}")
                    break
        finally:
            if self.control_client == websocket:
                self.control_client = None
                logger.info(f"Control client fully disconnected: {websocket.remote_address}")

    async def autonomy_handler(self, websocket):
        self.autonomy_client = websocket
        self.autonomy_connection_state = ConnectionState.CONNECTED
        logger.info(f"Autonomy client connected: {websocket.remote_address}")

        try:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.2)

                    if self.autonomy_connection_state != ConnectionState.CONNECTED:
                        self.autonomy_connection_state = ConnectionState.CONNECTED

                    data = json.loads(message)
                    mode = data.get("autonomy", "")

                    if mode:
                        self.teleop_decisin_manager.set_control_source(ControlSource.AUTONOMOUS)
                    else:
                        self.teleop_decisin_manager.set_control_source(ControlSource.USER)

                except asyncio.TimeoutError:
                    if self.autonomy_connection_state != ConnectionState.DISCONNECTED:
                        self.autonomy_connection_state = ConnectionState.DISCONNECTED

                    if self.teleop_decisin_manager.current_source != ControlSource.AUTONOMOUS:
                        self.teleop_decisin_manager.set_control_source(ControlSource.AUTONOMOUS)

                except websockets.exceptions.ConnectionClosed:
                    # The client actually closed the socket or network is gone
                    logger.info(f"Autonomy client disconnected: {websocket.remote_address}")
                    break
                except Exception as e:
                    logger.error(f"Error handling control connection: {e}")
                    break
        finally:
            if self.autonomy_client == websocket:
                self.autonomy_client = None
                self.autonomy_connection_state = ConnectionState.DISCONNECTED
                logger.info(f"Autonomy client fully disconnected: {websocket.remote_address}")

    async def video_handler(self, websocket):
        self.video_client = websocket
        logger.info(f"Video client connected: {websocket.remote_address}")
        try:
            await websocket.wait_closed()
        except asyncio.CancelledError:
            logger.info(f"Video handler cancelled for: {websocket.remote_address}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Video client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error in video connection: {e}")
        finally:
            if self.video_client == websocket:
                self.video_client = None
                logger.info(f"Video client fully disconnected: {websocket.remote_address}")

    async def telemetry_handler(self, websocket):
        self.telemetry_client = websocket
        logger.info(f"Telemetry client connected: {websocket.remote_address}")
        try:
            while True:
                wifi_details = get_wifi_details()
                telemetry = {
                    "ap_mac": wifi_details.get("ap_mac", ""),
                    "signal_strength": wifi_details.get("signal_strength", 0),
                    "user_mode": self.teleop_decisin_manager.select_active_source().value,
                    "back_connection": self.control_client is not None
                }

                await websocket.send(json.dumps(telemetry))
                await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Telemetry client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error in telemetry handler: {e}")
        finally:
            if self.telemetry_client == websocket:
                self.telemetry_client = None
                logger.info(f"Telemetry client fully disconnected: {websocket.remote_address}")

    async def _on_control_message(self, websocket, message: str):
        try:
            data = json.loads(message)
            throttle = data.get("throttle", 0.0)
            angle = data.get("angle", 0.0)
            self.teleop_decisin_manager.update_user_input(throttle, angle)
        except Exception as e:
            logger.error(f"Unhandled error in control message: {e}")
            await websocket.send(json.dumps({"error": "Server error"}))
