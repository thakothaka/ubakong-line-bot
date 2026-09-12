import os
import re
import hmac
import hashlib
import base64
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import PlainTextResponse

from ubakong import (
    method1_day_time,
    method2_phase_time,
    method3_lunar_day_time,
    compare_all_three,
    format_result,
)

app = FastAPI(title="Ubakong LINE Bot")

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_API = "https://api.line.me/v2/bot/message/reply"


HELP_TEXT = """🔮 Ubakong Bot

ส่งข้อความได้ 4 แบบ:

1️⃣ วัน + เวลา
1 2026-09-15 14:30

2️⃣ ขึ้น/แรม + เวลา
2 2026-09-15 14:30 ขึ้น
หรือ
2 2026-09-15 14:30 แรม

3️⃣ ดิถีค่ำ + เวลา
3 2026-09-15 14:30 7

🔄 เปรียบเทียบทั้ง 3 วิธี
all 2026-09-15 14:30 ขึ้น 7

พิมพ์ help เพื่อดูวิธีใช้อีกครั้ง
"""


@app.get("/")
async def home():
    return {
        "status": "ok",
        "service": "Ubakong LINE Bot",
        "message": "Bot is running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


def verify_line_signature(body: bytes, signature: str | None) -> bool:
    if not LINE_CHANNEL_SECRET or not signature:
        return False

    digest = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
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
                "text": text[:5000]
            }
        ],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            LINE_REPLY_API,
            headers=headers,
            json=payload
        )
        response.raise_for_status()


def parse_datetime(date_text: str, time_text: str) -> datetime:
    return datetime.strptime(
        f"{date_text} {time_text}",
        "%Y-%m-%d %H:%M"
    )


def process_user_text(text: str) -> str:
    text = text.strip()

    if text.lower() in {"help", "menu", "วิธีใช้", "ช่วย"}:
        return HELP_TEXT

    # Method 1
    m = re.fullmatch(
        r"1\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        dt = parse_datetime(m.group(1), m.group(2))
        return format_result(method1_day_time(dt))

    # Method 2
    m = re.fullmatch(
        r"2\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s+(ขึ้น|แรม|waxing|waning|wax|wane)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        dt = parse_datetime(m.group(1), m.group(2))
        return format_result(method2_phase_time(dt, m.group(3)))

    # Method 3
    m = re.fullmatch(
        r"3\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2})",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        dt = parse_datetime(m.group(1), m.group(2))
        lunar_day = int(m.group(3))
        return format_result(method3_lunar_day_time(dt, lunar_day))

    # All three
    m = re.fullmatch(
        r"all\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s+(ขึ้น|แรม|waxing|waning|wax|wane)\s+(\d{1,2})",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        dt = parse_datetime(m.group(1), m.group(2))
        phase = m.group(3)
        lunar_day = int(m.group(4))
        return compare_all_three(dt, phase, lunar_day)

    return "รูปแบบข้อความยังไม่ถูกต้องครับ\n\n" + HELP_TEXT


@app.post("/webhook")
async def webhook(
    request: Request,
    x_line_signature: str | None = Header(default=None)
):
    body = await request.body()

    # LINE recommends verifying the signature before processing events.
    if not verify_line_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid LINE signature")

    payload = await request.json()

    for event in payload.get("events", []):
        if event.get("type") != "message":
            continue

        message = event.get("message", {})
        if message.get("type") != "text":
            continue

        reply_token = event.get("replyToken")
        user_text = message.get("text", "")

        try:
            answer = process_user_text(user_text)
        except ValueError as e:
            answer = f"ข้อมูลไม่ถูกต้อง: {e}\n\n{HELP_TEXT}"
        except Exception:
            answer = "เกิดข้อผิดพลาดในการคำนวณ กรุณาลองใหม่อีกครั้ง"

        if reply_token:
            await reply_line(reply_token, answer)

    return PlainTextResponse("OK")


# Local test endpoints; useful before connecting LINE.
@app.get("/test/method1")
async def test_method1(date: str, time: str):
    dt = parse_datetime(date, time)
    return method1_day_time(dt)


@app.get("/test/method2")
async def test_method2(date: str, time: str, phase: str):
    dt = parse_datetime(date, time)
    return method2_phase_time(dt, phase)


@app.get("/test/method3")
async def test_method3(date: str, time: str, lunar_day: int):
    dt = parse_datetime(date, time)
    return method3_lunar_day_time(dt, lunar_day)
