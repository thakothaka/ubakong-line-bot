"""
Run this ONCE from your computer after deployment to create
a one-button LINE Rich Menu using the Messaging API.

Requirements:
    pip install httpx pillow

Environment:
    LINE_CHANNEL_ACCESS_TOKEN=...

This script:
1) Creates a 2500 x 843 one-button rich menu.
2) Generates a simple rich-menu PNG.
3) Uploads the image.
4) Sets it as the default rich menu.

You can replace rich_menu.png later with your own design.
"""

import os
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
if not TOKEN:
    raise RuntimeError("Set LINE_CHANNEL_ACCESS_TOKEN first.")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

CREATE_URL = "https://api.line.me/v2/bot/richmenu"
UPLOAD_BASE = "https://api-data.line.me/v2/bot/richmenu"
DEFAULT_BASE = "https://api.line.me/v2/bot/user/all/richmenu"

OUT = Path("rich_menu.png")


def make_image():
    w, h = 2500, 843
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    # Simple black-on-white design. Replace with your own branding anytime.
    draw.rounded_rectangle(
        (80, 80, w - 80, h - 80),
        radius=60,
        outline="black",
        width=12,
    )

    try:
        font_big = ImageFont.truetype("arial.ttf", 120)
        font_small = ImageFont.truetype("arial.ttf", 62)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    title = "CHECK MY LUCK NOW"
    sub = "Tap once • Ubakong 3 methods • Next four-dot period"

    tb = draw.textbbox((0, 0), title, font=font_big)
    sb = draw.textbbox((0, 0), sub, font=font_small)

    draw.text(
        ((w - (tb[2] - tb[0])) / 2, 290),
        title,
        fill="black",
        font=font_big,
    )
    draw.text(
        ((w - (sb[2] - sb[0])) / 2, 490),
        sub,
        fill="black",
        font=font_small,
    )

    img.save(OUT, "PNG")
    print(f"Created {OUT}")


def create_menu() -> str:
    payload = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "Ubakong Check Now",
        "chatBarText": "Check My Luck",
        "areas": [
            {
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": 2500,
                    "height": 843,
                },
                "action": {
                    "type": "postback",
                    "label": "Check My Luck",
                    "data": "action=check_now",
                    "displayText": "🔮 Check My Luck Now",
                },
            }
        ],
    }

    r = httpx.post(CREATE_URL, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    rich_menu_id = r.json()["richMenuId"]
    print("Rich menu ID:", rich_menu_id)
    return rich_menu_id


def upload_image(rich_menu_id: str):
    with OUT.open("rb") as f:
        r = httpx.post(
            f"{UPLOAD_BASE}/{rich_menu_id}/content",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "image/png",
            },
            content=f.read(),
            timeout=30,
        )
    r.raise_for_status()
    print("Image uploaded")


def set_default(rich_menu_id: str):
    r = httpx.post(
        f"{DEFAULT_BASE}/{rich_menu_id}",
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=30,
    )
    r.raise_for_status()
    print("Default rich menu set")


if __name__ == "__main__":
    make_image()
    menu_id = create_menu()
    upload_image(menu_id)
    set_default(menu_id)
    print("Done. Open your LINE OA and test the button.")
