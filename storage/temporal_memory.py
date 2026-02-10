from collections import deque
import time

class TemporalMemory:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history = {}  # entity_id -> deque[(timestamp, risk)]

    def record(self, entity_id, risk):
        if entity_id not in self.history:
            self.history[entity_id] = deque(maxlen=self.window_size)
        self.history[entity_id].append((time.time(), risk))

    def get_history(self, entity_id):
        return list(self.history.get(entity_id, []))
