from flask import Flask, jsonify, request
from threading import Thread
from flask_cors import CORS


class ControlAPIHandler:
    """
    A lightweight Flask-based HTTP API handler for interacting with
    the car's control state.

    Provides endpoints for toggling and querying:
    - recording state (/recording)
    - autonomy mode (/autonomy)
    """
    def __init__(self, teleop_control_part):
        self.teleop_control_part = teleop_control_part
        self.flask_app = Flask(__name__)
        CORS(self.flask_app)
        self.setup_routes()

    def setup_routes(self):
        self.flask_app.add_url_rule('/ping', 'ping', self.ping, methods=['GET'])
        self.flask_app.add_url_rule('/recording', 'get_recording', self.get_recording, methods=['GET'])
        self.flask_app.add_url_rule('/recording', 'toggle_recording', self.toggle_recording, methods=['POST'])
        self.flask_app.add_url_rule('/autonomy', 'get_autonomy', self.get_autonomy, methods=['GET'])
        self.flask_app.add_url_rule('/autonomy', 'set_autonomy', self.set_autonomy, methods=['POST'])

    def start(self):
        Thread(target=lambda: self.flask_app.run(host="0.0.0.0", port=8081, debug=False, use_reloader=False), daemon=True).start()

    def ping(self):
        print(">>> /ping HIT")
        return jsonify({"status": "ok"})

    def toggle_recording(self):
        self.teleop_control_part.teleop_decision_manager.recording_enabled = not self.teleop_control_part.teleop_decision_manager.recording_enabled
        return jsonify({"recording": self.teleop_control_part.teleop_decision_manager.recording_enabled})

    def get_recording(self):
        try:
            print(">>> GET /recording")
            return jsonify({"recording": self.teleop_control_part.teleop_decision_manager.recording_enabled})
        except Exception as e:
            print(f"❌ ERROR in /recording: {e}")
            return jsonify({"error": str(e)}), 500

    def set_autonomy(self):
        try:
            data = request.get_json()
            new_value = data.get("autonomy")
            if new_value is None:
                return jsonify({"error": "Missing autonomy value"}), 400
            self.teleop_control_part.teleop_decision_manager.autonomy_enabled = bool(new_value)
            return jsonify({"autonomy": self.teleop_control_part.teleop_decision_manager.autonomy_enabled})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def get_autonomy(self):
        return jsonify({"autonomy": self.teleop_control_part.teleop_decision_manager.autonomy_enabled})