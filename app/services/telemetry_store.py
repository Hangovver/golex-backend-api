
from collections import deque
import threading, json, time, os

class TelemetryStore:
    def __init__(self, maxlen:int=5000, logfile:str|None=None):
        self.buf = deque(maxlen=maxlen)
        self.lock = threading.Lock()
        self.logfile = logfile or os.getenv("TELEMETRY_LOG","/tmp/golex_telemetry.log")

    def add_many(self, events:list[dict]):
        ts = int(time.time()*1000)
        with self.lock:
            for e in events:
                e = dict(e)
                e.setdefault("ts", ts)
                self.buf.append(e)
            try:
                with open(self.logfile, "a", encoding="utf-8") as f:
                    for e in events:
                        f.write(json.dumps(e, ensure_ascii=False) + "\n")
            except Exception:
                pass

    def last(self, n:int=100)->list[dict]:
        with self.lock:
            return list(self.buf)[-n:]

STORE = TelemetryStore()
