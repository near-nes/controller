import time
from collections import deque
from contextlib import contextmanager
from timeit import default_timer as timer


class Profile:
    def __init__(self, max_history=1000):
        self.total_time = 0.0
        self.times = deque(maxlen=max_history)
        self.count = 0
        self._start_time = None

    @contextmanager
    def time(self):
        start = time.perf_counter()
        try:
            yield self
        finally:
            elapsed = time.perf_counter() - start
            self.times.append(elapsed)
            self.total_time += elapsed
            self.count += 1

    def start(self):
        self._start_time = time.perf_counter()

    def end(self):
        if self._start_time is not None:
            elapsed = time.perf_counter() - self._start_time
            self.times.append(elapsed)
            self.total_time += elapsed
            self.count += 1
            self._start_time = None
