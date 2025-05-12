# resource_monitor.py

import threading
import time

from services.experiment_logger import ExperimentLogger


class ResourceMonitor:
    """
    Periodically monitors and logs system resource usage (CPU, memory)
    using the ExperimentLogger for performance diagnostics.
    """
    def __init__(self, logger: ExperimentLogger, bssid_poll_interval=1.0, resource_poll_interval=1.0):
        self.resource_thread = None
        self.bssid_thread = None
        self.logger = logger
        self.bssid_poll_interval = bssid_poll_interval
        self.resource_poll_interval = resource_poll_interval
        self.last_bssid = None
        self.running = False

    def _bssid_loop(self):
        while self.running:
            current_bssid = self.logger.get_current_bssid()
            if current_bssid and current_bssid != self.last_bssid:
                self.logger.log_ap_switch(current_bssid)
                self.last_bssid = current_bssid
            time.sleep(self.bssid_poll_interval)

    def _resource_loop(self):
        while self.running:
            self.logger.log_resource_usage()
            time.sleep(self.resource_poll_interval)

    def start(self):
        self.running = True
        self.bssid_thread = threading.Thread(target=self._bssid_loop, daemon=True)
        self.resource_thread = threading.Thread(target=self._resource_loop, daemon=True)
        self.bssid_thread.start()
        self.resource_thread.start()

    def stop(self):
        self.running = False
        self.bssid_thread.join()
        self.resource_thread.join()
