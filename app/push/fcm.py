import os, httpx
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")
FCM_URL = "https://fcm.googleapis.com/fcm/send"  # Legacy HTTP; for production migrate to HTTP v1

headers = {
    "Authorization": f"key={FCM_SERVER_KEY}",
    "Content-Type": "application/json",
}

async def send_to_token(token: str, title: str, body: str, data: dict | None = None):
    payload = {"to": token, "notification": {"title": title, "body": body}, "data": data or {}}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(FCM_URL, headers=headers, json=payload)
        return r.status_code, r.text

async def send_to_topic(topic: str, title: str, body: str, data: dict | None = None):
    payload = {"to": f"/topics/{topic}", "notification": {"title": title, "body": body}, "data": data or {}}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(FCM_URL, headers=headers, json=payload)
        return r.status_code, r.text
