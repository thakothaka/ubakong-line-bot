import os
import hmac
import hashlib
import base64

import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import PlainTextResponse

from ubakong_engine import format_check_now

app = FastAPI(title="Ubakong LINE Bot v2")

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_API = "https://api.line.me/v2/bot/message/reply"


@app.get("/")
async def home():
    return {
        "status": "ok",
        "service": "Ubakong LINE Bot v2",
        "mode": "one-button",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/preview")
async def preview():
    """
    Browser test: lets you see the same text LINE will receive.
    """
    return PlainTextResponse(format_check_now())


def verify_line_signature(body: bytes, signature: str | None) -> bool:
    if not LINE_CHANNEL_SECRET or not signature:
        return False

    digest = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()

    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)


async def reply_line(reply_token: str, text: str):
    if not LINE_CHANNEL_ACCESS_TOKEN:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN is not configured")

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text[:5000],
            }
        ],
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            LINE_REPLY_API,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str | None = Header(default=None),
):
    body = await request.body()

    if not verify_line_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid LINE signature")

    payload = await request.json()

    for event in payload.get("events", []):
        event_type = event.get("type")
        reply_token = event.get("replyToken")

        # Primary UX: Rich Menu postback button.
        if event_type == "postback":
            data = event.get("postback", {}).get("data", "")
            if data == "action=check_now" and reply_token:
                try:
                    await reply_line(reply_token, format_check_now())
                except Exception:
                    await reply_line(
                        reply_token,
                        "เกิดข้อผิดพลาดในการคำนวณ กรุณาลองใหม่อีกครั้ง",
                    )
            continue

        # Optional fallback:
        # If user types anything, treat it like pressing the button.
        if event_type == "message":
            message = event.get("message", {})
            if message.get("type") == "text" and reply_token:
                try:
                    await reply_line(reply_token, format_check_now())
                except Exception:
                    await reply_line(
                        reply_token,
                        "เกิดข้อผิดพลาดในการคำนวณ กรุณาลองใหม่อีกครั้ง",
                    )

    return PlainTextResponse("OK")
