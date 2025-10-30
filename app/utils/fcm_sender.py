import os, json, httpx

FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")

def _norm_topic(t:str)->str:
    return t.replace(':','_')

def _headers():
    if not FCM_SERVER_KEY:
        raise RuntimeError("FCM_SERVER_KEY env missing")
    return {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }

async def send_to_token(token: str, title: str, body: str, data: dict):
    payload = {
        "to": token,
        "notification": {"title": title, "body": body},
        "data": data
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(FCM_ENDPOINT, headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()

async def send_to_topic(topic: str, title: str, body: str, data: dict):
    if not topic.startswith("/topics/"):
        topic = f"/topics/{topic}"
    payload = {
        "to": f"/topics/{_norm_topic(topic)}",
        "notification": {"title": title, "body": body},
        "data": data
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(FCM_ENDPOINT, headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()
