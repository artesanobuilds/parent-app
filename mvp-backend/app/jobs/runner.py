"""Small shared periodic recovery loop, independent of occupied worker slots."""
import logging
import threading

logger = logging.getLogger(__name__)


class JobReaper:
    def __init__(self, storage, kind, interval=1.0):
        self.storage, self.kind, self.interval = storage, kind, interval
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True,
                                       name=f'{self.kind}-reaper')
        self.thread.start()

    def _loop(self):
        while not self.stop_event.wait(self.interval):
            try:
                self.storage.reap_expired_job_attempts(self.kind)
            except Exception:
                logger.exception('job reaper failed (%s)', self.kind)

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(2)
