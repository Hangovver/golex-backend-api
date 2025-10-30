import http.client, json, smtplib
from email.message import EmailMessage
from typing import Dict

class SlackProvider:
    def __init__(self, webhook_url: str): self.webhook_url = webhook_url
    def send(self, text: str) -> Dict:
        # demo: do nothing, return pretend ok
        return {"sent":"slack", "ok": True}

class EmailProvider:
    def __init__(self, smtp_host: str, sender: str, to: str): self.smtp_host=smtp_host; self.sender=sender; self.to=to
    def send(self, text: str) -> Dict:
        # demo: no-op
        return {"sent":"email", "ok": True}

class WebhookProvider:
    def __init__(self, url: str): self.url=url
    def send(self, text: str) -> Dict:
        # demo: no-op
        return {"sent":"webhook", "ok": True}
