
from collections import deque
import threading, time, json, os

class FeedbackStore:
    def __init__(self, maxlen:int=5000, logfile:str|None=None):
      self.buf = deque(maxlen=maxlen)
      self.lock = threading.Lock()
      self.logfile = logfile or os.getenv("FEEDBACK_LOG","/tmp/golex_feedback.log")

    def add(self, rating:int, comment:str, meta:dict|None=None):
      item = {"ts": int(time.time()*1000), "rating": int(rating), "comment": str(comment or "")[:2000], "meta": meta or {}}
      with self.lock:
        self.buf.append(item)
        try:
          with open(self.logfile,"a",encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False)+"\n")
        except Exception:
          pass

    def last(self, n:int=100):
      with self.lock:
        return list(self.buf)[-n:]

STORE = FeedbackStore()
