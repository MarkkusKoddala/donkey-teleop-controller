from aiohttp import web


class ControlAPIHandler:
    """
    A lightweight aiohttp-based HTTP API handler for interacting with
    the car's control state.

    Provides endpoints for toggling and querying:
    - recording state (/recording)
    - autonomy mode (/autonomy)

    """
    def __init__(self, control_manager):
        self.control_manager = control_manager
        self.sse_clients = []
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get('/recording', self.get_recording)
        self.app.router.add_post('/recording', self.toggle_recording)
        self.app.router.add_post('/autonomy', self.set_autonomy)
        self.app.router.add_get('/autonomy', self.get_autonomy)

    async def toggle_recording(self, request):
        self.control_manager.teleop_decisin_manager.recording_enabled = not self.control_manager.teleop_decisin_manager.recording_enabled
        return web.json_response({"recording": self.control_manager.teleop_decisin_manager.recording_enabled})

    async def get_recording(self, request):
        return web.json_response({"recording": self.control_manager.teleop_decisin_manager.recording_enabled})

    async def set_autonomy(self, request):
        try:
            data = await request.json()
            new_value = data.get("autonomy")
            if new_value is None:
                return web.json_response({"error": "Missing autonomy value"}, status=400)
            self.control_manager.teleop_decisin_manager.autonomy_enabled = bool(new_value)
            return web.json_response({"autonomy": self.control_manager.teleop_decisin_manager.autonomy_enabled})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def get_autonomy(self, request):
        return web.json_response({"autonomy": self.control_manager.teleop_decisin_manager.autonomy_enabled})

    def get_app(self):
        return self.app
