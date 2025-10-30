
import requests, os, json, sys

BASE = os.environ.get("GOLEX_API","http://localhost:8000/api/v1") if "api/v1" in os.environ.get("GOLEX_API","") else os.environ.get("GOLEX_API","http://localhost:8000")

def check():
    ok = True
    r = requests.get(f"{BASE}/leagues/1/context")
    ok &= (r.status_code==200)
    r = requests.get(f"{BASE}/leagues/1/fixtures?type=upcoming&limit=2")
    ok &= (r.status_code==200)
    etag = r.headers.get("ETag")
    if etag:
        r2 = requests.get(f"{BASE}/leagues/1/fixtures?type=upcoming&limit=2", headers={"If-None-Match": etag})
        ok &= (r2.status_code in (200,304))
    r = requests.post(f"{BASE}/telemetry/events", json=[{"name":"acceptance","params":{"s5":True}}])
    ok &= (r.status_code==200)
    print("S5 CHECK:", "PASS" if ok else "FAIL")

if __name__=="__main__":
    check()
