# Ubakong LINE Bot

A simple LINE Official Account bot that calculates traditional Ubakong timing using 3 methods.

## Commands

### Method 1: day + time
```
1 2026-09-15 14:30
```

### Method 2: waxing/waning + time
```
2 2026-09-15 14:30 ขึ้น
2 2026-09-15 14:30 แรม
```

### Method 3: lunar day + time
```
3 2026-09-15 14:30 7
```

### Compare all 3
```
all 2026-09-15 14:30 ขึ้น 7
```

## Run locally

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install:
```bash
pip install -r requirements.txt
```

Run:
```bash
uvicorn main:app --reload
```

Open:
```
http://127.0.0.1:8000/docs
```

## Render

Build command:
```
pip install -r requirements.txt
```

Start command:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Add these environment variables in Render:
- LINE_CHANNEL_SECRET
- LINE_CHANNEL_ACCESS_TOKEN

Then set your LINE webhook URL to:
```
https://YOUR-SERVICE.onrender.com/webhook
```
