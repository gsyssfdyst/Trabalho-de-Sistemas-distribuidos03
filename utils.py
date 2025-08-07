import threading
import time

class LamportClock:
    def __init__(self):
        self.time = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.time += 1

    def update(self, received_time):
        with self.lock:
            self.time = max(self.time, received_time)

def log_event(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")
