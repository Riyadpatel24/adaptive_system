import threading
import time

def cpu_spike(duration=10):

    def spike():
        end = time.time() + duration
        while time.time() < end:
            pass

    thread = threading.Thread(target=spike)
    thread.start()


def memory_leak(duration=10):

    def leak():
        a = []
        end = time.time() + duration

        while time.time() < end:
            a.append("leak" * 1000)

    thread = threading.Thread(target=leak)
    thread.start()