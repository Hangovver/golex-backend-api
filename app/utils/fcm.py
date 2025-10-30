import os, json, aiohttp, asyncio

FCM_URL = "https://fcm.googleapis.com/fcm/send"
SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY", "")

async def send_to_token(token: str, title: str, body: str, data: dict | None = None):
    if not SERVER_KEY:
        return {"ok": False, "reason": "missing_server_key"}
    payload = {
        "to": token,
        "notification": {"title": title, "body": body},
        "data": data or {}
    }
    headers = {"Authorization": f"key={SERVER_KEY}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as s:
        async with s.post(FCM_URL, headers=headers, json=payload, timeout=5) as resp:
            try:
                return await resp.json()
            except Exception:
                return {"ok": resp.status}

async def send_to_topic(topic: str, title: str, body: str, data: dict | None = None):
    return await send_to_token(f"/topics/{topic}", title, body, data)
