# Logger.py

import json
import os
import subprocess
import time

import psutil


class ExperimentLogger:
    """
    Logs key runtime events such as control mode switches, Wi-Fi AP changes,
    and system resource usage to a JSONL file for later analysis.
    """
    def __init__(self, base_dir="/home/pi/minicar_back/logs", log_name="experiment_log.jsonl"):
        os.makedirs(base_dir, exist_ok=True)
        self.log_file = os.path.join(base_dir, log_name)

    def _write(self, entry: dict):
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
            f.flush()

    def log_ap_switch(self, bssid: str):
        entry = {
            "type": "ap_switch",
            "bssid": bssid,
            "timestamp": int(time.time() * 1000)
        }
        self._write(entry)

    def log_resource_usage(self):
        entry = {
            "type": "sys",
            "cpu": psutil.cpu_percent(interval=None),
            "mem_mb": psutil.virtual_memory().used / (1024 ** 2),
            "timestamp": int(time.time() * 1000)
        }
        self._write(entry)

    def log_mode_switch(self, mode: str):
        entry = {
            "type": "mode_auto_switch",
            "mode": mode,
            "timestamp": int(time.time() * 1000)
        }
        self._write(entry)

    @staticmethod
    def get_current_bssid(interface="wlan0") -> str:
        try:
            output = subprocess.check_output(["iwconfig", interface]).decode()
            for line in output.splitlines():
                if "Access Point" in line:
                    parts = line.strip().split()
                    for part in parts:
                        if ":" in part and len(part.split(":")) == 6:
                            return part  # Return BSSID
        except Exception as e:
            print(f"Error reading BSSID: {e}")
        return "unknown"

