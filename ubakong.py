from datetime import datetime, timedelta
from typing import Dict

# ------------------------------------------------------------
# Ubakong symbols / meanings
# Reference pattern based on the traditional 7 x 5 table.
# ------------------------------------------------------------

RESULTS: Dict[str, dict] = {
    "four_zero": {
        "thai": "สี่ศูนย์",
        "emoji": "🟢🟢",
        "rating": 5,
        "summary": "ดีมาก",
        "detail": "ตามตำราเป็นยามที่ดีมาก เหมาะกับการเดินทางหรือทำการสำคัญ",
    },
    "two_zero": {
        "thai": "สองศูนย์",
        "emoji": "🟢",
        "rating": 4,
        "summary": "ดี",
        "detail": "ตามตำราเป็นยามที่ดี เหมาะกับการเริ่มต้นหรือเดินทาง",
    },
    "clear": {
        "thai": "ปลอดศูนย์",
        "emoji": "🟡",
        "rating": 3,
        "summary": "กลาง ๆ",
        "detail": "ตามตำราเป็นยามกลาง ๆ ไม่มีลาภเด่น แต่ไม่มีเคราะห์เด่น",
    },
    "one_zero": {
        "thai": "ศูนย์หนึ่ง",
        "emoji": "🔴",
        "rating": 2,
        "summary": "ควรระวัง",
        "detail": "ตามตำราไม่ใช่ยามที่เหมาะ หากเลือกเวลาอื่นได้ควรพิจารณาเวลาอื่น",
    },
    "cross": {
        "thai": "กากบาท",
        "emoji": "⛔",
        "rating": 1,
        "summary": "ไม่แนะนำ",
        "detail": "ตามตำราเป็นยามที่ควรหลีกเลี่ยงสำหรับการเดินทางหรือทำการสำคัญ",
    },
}

# Columns: 0=เช้า, 1=สาย, 2=เที่ยง, 3=บ่าย, 4=เย็น
# Night uses the same column positions:
# 0=18:01-20:24, 1=20:25-22:48, 2=22:49-01:12,
# 3=01:13-03:36, 4=03:37-06:00
TABLE_7X5 = {
    6: ["four_zero", "cross",     "clear",     "two_zero",  "one_zero"],  # Sunday
    0: ["one_zero",  "four_zero", "cross",     "clear",     "two_zero"],  # Monday
    1: ["two_zero",  "one_zero",  "four_zero", "cross",     "clear"],     # Tuesday
    2: ["clear",     "two_zero",  "one_zero",  "four_zero", "cross"],     # Wednesday
    3: ["cross",     "clear",     "two_zero",  "one_zero",  "four_zero"], # Thursday
    4: ["four_zero", "cross",     "clear",     "two_zero",  "one_zero"],  # Friday
    5: ["one_zero",  "four_zero", "cross",     "clear",     "two_zero"],  # Saturday
}

# Method 3 uses a 5 x 5 form equivalent to the first five patterns.
TABLE_5X5 = [
    ["four_zero", "cross",     "clear",     "two_zero",  "one_zero"],  # row 1
    ["one_zero",  "four_zero", "cross",     "clear",     "two_zero"],  # row 2
    ["two_zero",  "one_zero",  "four_zero", "cross",     "clear"],     # row 3
    ["clear",     "two_zero",  "one_zero",  "four_zero", "cross"],     # row 4
    ["cross",     "clear",     "two_zero",  "one_zero",  "four_zero"], # row 5
]

DAY_NAMES_TH = {
    0: "วันจันทร์",
    1: "วันอังคาร",
    2: "วันพุธ",
    3: "วันพฤหัสบดี",
    4: "วันศุกร์",
    5: "วันเสาร์",
    6: "วันอาทิตย์",
}


def _minute_of_day(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def _period_info(dt: datetime) -> dict:
    """
    Return the Ubakong column (0..4), period label, and whether it is day/night.

    Boundaries:
      06:01-08:24 => col 0
      08:25-10:48 => col 1
      10:49-13:12 => col 2
      13:13-15:36 => col 3
      15:37-18:00 => col 4

      18:01-20:24 => col 0
      20:25-22:48 => col 1
      22:49-01:12 => col 2
      01:13-03:36 => col 3
      03:37-06:00 => col 4
    """
    m = _minute_of_day(dt)

    # Day periods
    if 361 <= m <= 504:
        return {"column": 0, "label": "เช้า 06:01–08:24", "is_night": False}
    if 505 <= m <= 648:
        return {"column": 1, "label": "สาย 08:25–10:48", "is_night": False}
    if 649 <= m <= 792:
        return {"column": 2, "label": "เที่ยง 10:49–13:12", "is_night": False}
    if 793 <= m <= 936:
        return {"column": 3, "label": "บ่าย 13:13–15:36", "is_night": False}
    if 937 <= m <= 1080:
        return {"column": 4, "label": "เย็น 15:37–18:00", "is_night": False}

    # Night periods
    if 1081 <= m <= 1224:
        return {"column": 0, "label": "กลางคืนยาม 1 18:01–20:24", "is_night": True}
    if 1225 <= m <= 1368:
        return {"column": 1, "label": "กลางคืนยาม 2 20:25–22:48", "is_night": True}
    if m >= 1369 or m <= 72:
        return {"column": 2, "label": "กลางคืนยาม 3 22:49–01:12", "is_night": True}
    if 73 <= m <= 216:
        return {"column": 3, "label": "กลางคืนยาม 4 01:13–03:36", "is_night": True}
    if 217 <= m <= 360:
        return {"column": 4, "label": "กลางคืนยาม 5 03:37–06:00", "is_night": True}

    raise ValueError("Unable to map time to an Ubakong period.")


def _astrological_day(dt: datetime) -> datetime:
    """
    Traditional day changes at sunrise / about 06:00.
    Times from 00:00 through 06:00 belong to the preceding day.
    06:01 onward uses the civil date.
    """
    if _minute_of_day(dt) <= 360:
        return dt - timedelta(days=1)
    return dt


def _decorate(base: dict, method: int, dt: datetime, extra: dict | None = None) -> dict:
    result = RESULTS[base["code"]].copy()
    output = {
        "method": method,
        "datetime": dt,
        "period": base["period"],
        "code": base["code"],
        **result,
    }
    if extra:
        output.update(extra)
    return output


def method1_day_time(dt: datetime) -> dict:
    """
    Method 1: day + time.
    """
    astro_dt = _astrological_day(dt)
    weekday = astro_dt.weekday()
    period = _period_info(dt)
    code = TABLE_7X5[weekday][period["column"]]

    return _decorate(
        {"code": code, "period": period["label"]},
        method=1,
        dt=dt,
        extra={
            "astro_weekday": DAY_NAMES_TH[weekday],
            "astro_date": astro_dt.date().isoformat(),
        },
    )


def method2_phase_time(dt: datetime, phase: str) -> dict:
    """
    Method 2: day + waxing/waning + time.

    phase:
      'waxing' / 'ขึ้น'
      'waning' / 'แรม'

    The waxing phase uses the normal column order.
    The waning phase reverses the 5 columns.
    """
    phase_norm = phase.strip().lower()
    if phase_norm in {"ขึ้น", "waxing", "wax", "up"}:
        phase_name = "ข้างขึ้น"
        reverse = False
    elif phase_norm in {"แรม", "waning", "wane", "down"}:
        phase_name = "ข้างแรม"
        reverse = True
    else:
        raise ValueError("phase must be ขึ้น/waxing or แรม/waning")

    astro_dt = _astrological_day(dt)
    weekday = astro_dt.weekday()
    period = _period_info(dt)
    col = period["column"]
    if reverse:
        col = 4 - col

    code = TABLE_7X5[weekday][col]

    return _decorate(
        {"code": code, "period": period["label"]},
        method=2,
        dt=dt,
        extra={
            "phase": phase_name,
            "astro_weekday": DAY_NAMES_TH[weekday],
            "astro_date": astro_dt.date().isoformat(),
        },
    )


def method3_lunar_day_time(dt: datetime, lunar_day: int) -> dict:
    """
    Method 3: lunar day (ดิถีค่ำ) + time.

    lunar_day is counted 1..15 for Thai waxing/waning dates.
    The row cycles every 5 days:
       1,6,11 -> row 1
       2,7,12 -> row 2
       ...
       5,10,15 -> row 5

    For night periods, the time-column order is reversed.
    """
    if not 1 <= lunar_day <= 15:
        raise ValueError("lunar_day must be between 1 and 15")

    row = (lunar_day - 1) % 5
    period = _period_info(dt)
    col = period["column"]

    if period["is_night"]:
        col = 4 - col

    code = TABLE_5X5[row][col]

    return _decorate(
        {"code": code, "period": period["label"]},
        method=3,
        dt=dt,
        extra={
            "lunar_day": lunar_day,
            "row": row + 1,
        },
    )


def format_result(result: dict) -> str:
    stars = "⭐" * result["rating"]
    method_names = {
        1: "วิธีที่ 1: วัน + เวลา",
        2: "วิธีที่ 2: ข้างขึ้น/แรม + เวลา",
        3: "วิธีที่ 3: ดิถีค่ำ + เวลา",
    }

    lines = [
        "🔮 ยามอุบากอง",
        method_names[result["method"]],
        "",
        f"📅 {result['datetime'].strftime('%Y-%m-%d')}",
        f"🕒 {result['datetime'].strftime('%H:%M')}",
        f"⏱ {result['period']}",
    ]

    if result["method"] in (1, 2):
        lines.append(f"📌 วันตามยาม: {result['astro_weekday']}")
    if result["method"] == 2:
        lines.append(f"🌙 {result['phase']}")
    if result["method"] == 3:
        lines.append(f"🌙 ดิถี: {result['lunar_day']} ค่ำ")

    lines += [
        "",
        f"{result['emoji']} {result['thai']} — {result['summary']}",
        stars,
        result["detail"],
        "",
        "หมายเหตุ: ยามอุบากองเป็นความเชื่อและภูมิปัญญาโบราณ โปรดใช้ประกอบการตัดสินใจเท่านั้น",
    ]
    return "\n".join(lines)


def compare_all_three(dt: datetime, phase: str, lunar_day: int) -> str:
    results = [
        method1_day_time(dt),
        method2_phase_time(dt, phase),
        method3_lunar_day_time(dt, lunar_day),
    ]

    lines = [
        "🔮 เปรียบเทียบยามอุบากอง 3 วิธี",
        f"📅 {dt.strftime('%Y-%m-%d')}  🕒 {dt.strftime('%H:%M')}",
        "",
    ]

    labels = ["① วัน+เวลา", "② ขึ้น/แรม+เวลา", "③ ดิถีค่ำ+เวลา"]
    for label, r in zip(labels, results):
        lines.append(
            f"{label}: {r['emoji']} {r['thai']} ({r['rating']}/5)"
        )

    avg = sum(r["rating"] for r in results) / 3
    lines += [
        "",
        f"คะแนนเฉลี่ย: {avg:.1f}/5",
        "",
        "หมายเหตุ: เป็นความเชื่อและภูมิปัญญาโบราณ โปรดใช้ประกอบการตัดสินใจเท่านั้น",
    ]
    return "\n".join(lines)
