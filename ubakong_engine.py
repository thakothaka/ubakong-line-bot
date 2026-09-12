from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import Callable

# pythaidate 0.2.0
from pythaidate import CsDate

try:
    from pythaidate import date_to_julianday
except ImportError:
    from pythaidate.julianday import date_to_julianday


BANGKOK = ZoneInfo("Asia/Bangkok")

RESULTS = {
    "four_zero": {
        "thai": "สี่ศูนย์",
        "emoji": "🟢🟢",
        "score": 5,
        "summary": "ดีมาก",
    },
    "two_zero": {
        "thai": "สองศูนย์",
        "emoji": "🟢",
        "score": 4,
        "summary": "ดี",
    },
    "clear": {
        "thai": "ปลอดศูนย์",
        "emoji": "🟡",
        "score": 3,
        "summary": "กลาง ๆ",
    },
    "one_zero": {
        "thai": "ศูนย์หนึ่ง",
        "emoji": "🟠",
        "score": 2,
        "summary": "ควรระวัง",
    },
    "cross": {
        "thai": "กากบาท",
        "emoji": "🔴",
        "score": 1,
        "summary": "ควรหลีกเลี่ยง",
    },
}

DAY_NAMES_TH = {
    0: "จันทร์",
    1: "อังคาร",
    2: "พุธ",
    3: "พฤหัสบดี",
    4: "ศุกร์",
    5: "เสาร์",
    6: "อาทิตย์",
}

# 7 x 5 traditional Ubakong table.
# Column order for daytime:
# เช้า, สาย, เที่ยง, บ่าย, เย็น
#
# Night reuses the same 5 positions:
# ยาม1, ยาม2, ยาม3, ยาม4, ยาม5
TABLE_7X5 = {
    6: ["four_zero", "cross",     "clear",     "two_zero",  "one_zero"],  # Sunday
    0: ["one_zero",  "four_zero", "cross",     "clear",     "two_zero"],  # Monday
    1: ["two_zero",  "one_zero",  "four_zero", "cross",     "clear"],     # Tuesday
    2: ["clear",     "two_zero",  "one_zero",  "four_zero", "cross"],     # Wednesday
    3: ["cross",     "clear",     "two_zero",  "one_zero",  "four_zero"], # Thursday
    4: ["four_zero", "cross",     "clear",     "two_zero",  "one_zero"],  # Friday
    5: ["one_zero",  "four_zero", "cross",     "clear",     "two_zero"],  # Saturday
}

# Method 3 is the 5 x 5 reduced pattern.
TABLE_5X5 = [
    ["four_zero", "cross",     "clear",     "two_zero",  "one_zero"],
    ["one_zero",  "four_zero", "cross",     "clear",     "two_zero"],
    ["two_zero",  "one_zero",  "four_zero", "cross",     "clear"],
    ["clear",     "two_zero",  "one_zero",  "four_zero", "cross"],
    ["cross",     "clear",     "two_zero",  "one_zero",  "four_zero"],
]


@dataclass(frozen=True)
class Period:
    column: int
    label: str
    start: datetime
    end: datetime
    is_night: bool


def now_bangkok() -> datetime:
    return datetime.now(BANGKOK)


def _minute_of_day(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def _at(d: date, hh: int, mm: int) -> datetime:
    return datetime.combine(d, time(hh, mm), tzinfo=BANGKOK)


def period_for(dt: datetime) -> Period:
    """
    MyHora fixed 2h24m periods.

    06:01–08:24
    08:25–10:48
    10:49–13:12
    13:13–15:36
    15:37–18:00

    18:01–20:24
    20:25–22:48
    22:49–01:12
    01:13–03:36
    03:37–06:00
    """
    dt = dt.astimezone(BANGKOK)
    d = dt.date()
    m = _minute_of_day(dt)

    if 361 <= m <= 504:
        return Period(0, "เช้า 06:01–08:24", _at(d, 6, 1), _at(d, 8, 24), False)
    if 505 <= m <= 648:
        return Period(1, "สาย 08:25–10:48", _at(d, 8, 25), _at(d, 10, 48), False)
    if 649 <= m <= 792:
        return Period(2, "เที่ยง 10:49–13:12", _at(d, 10, 49), _at(d, 13, 12), False)
    if 793 <= m <= 936:
        return Period(3, "บ่าย 13:13–15:36", _at(d, 13, 13), _at(d, 15, 36), False)
    if 937 <= m <= 1080:
        return Period(4, "เย็น 15:37–18:00", _at(d, 15, 37), _at(d, 18, 0), False)

    if 1081 <= m <= 1224:
        return Period(0, "กลางคืนยาม 1 18:01–20:24", _at(d, 18, 1), _at(d, 20, 24), True)
    if 1225 <= m <= 1368:
        return Period(1, "กลางคืนยาม 2 20:25–22:48", _at(d, 20, 25), _at(d, 22, 48), True)

    if m >= 1369:
        return Period(
            2,
            "กลางคืนยาม 3 22:49–01:12",
            _at(d, 22, 49),
            _at(d + timedelta(days=1), 1, 12),
            True,
        )
    if m <= 72:
        return Period(
            2,
            "กลางคืนยาม 3 22:49–01:12",
            _at(d - timedelta(days=1), 22, 49),
            _at(d, 1, 12),
            True,
        )
    if 73 <= m <= 216:
        return Period(3, "กลางคืนยาม 4 01:13–03:36", _at(d, 1, 13), _at(d, 3, 36), True)
    if 217 <= m <= 360:
        return Period(4, "กลางคืนยาม 5 03:37–06:00", _at(d, 3, 37), _at(d, 6, 0), True)

    raise ValueError("Unable to map time to Ubakong period")


def astrological_date(dt: datetime) -> date:
    """
    Traditional day changes at about 06:00.
    00:00–06:00 belongs to the previous day.
    """
    local = dt.astimezone(BANGKOK)
    if _minute_of_day(local) <= 360:
        return local.date() - timedelta(days=1)
    return local.date()


def thai_lunar_info(dt: datetime) -> dict:
    """
    Convert the astrological date to the Thai lunisolar calendar.

    CsDate.day is the lunar day within the lunar month:
      1..15  => waxing
      16..30 => waning (subtract 15)
    """
    adate = astrological_date(dt)
    jd = date_to_julianday(adate)
    cs = CsDate.fromjulianday(jd)

    raw_day = int(cs.day)
    if raw_day <= 15:
        phase = "ขึ้น"
        lunar_day = raw_day
    else:
        phase = "แรม"
        lunar_day = raw_day - 15

    return {
        "phase": phase,
        "lunar_day": lunar_day,
        "month": int(cs.month),
        "cs_year": int(cs.year),
        "text": f"{phase} {lunar_day} ค่ำ",
        "full_text": str(cs),
    }


def _result(code: str, method: int, dt: datetime, period: Period, extra: dict | None = None) -> dict:
    base = RESULTS[code]
    data = {
        "method": method,
        "datetime": dt,
        "period": period,
        "code": code,
        **base,
    }
    if extra:
        data.update(extra)
    return data


def method1(dt: datetime) -> dict:
    p = period_for(dt)
    adate = astrological_date(dt)
    weekday = adate.weekday()
    code = TABLE_7X5[weekday][p.column]
    return _result(
        code,
        1,
        dt,
        p,
        {
            "astro_date": adate,
            "weekday": DAY_NAMES_TH[weekday],
        },
    )


def method2(dt: datetime) -> dict:
    """
    Day + waxing/waning + time.

    Waxing: normal time-column order.
    Waning: reverse the 5 time columns.
    """
    p = period_for(dt)
    adate = astrological_date(dt)
    weekday = adate.weekday()
    lunar = thai_lunar_info(dt)

    col = p.column if lunar["phase"] == "ขึ้น" else 4 - p.column
    code = TABLE_7X5[weekday][col]

    return _result(
        code,
        2,
        dt,
        p,
        {
            "astro_date": adate,
            "weekday": DAY_NAMES_TH[weekday],
            "phase": lunar["phase"],
            "lunar_day": lunar["lunar_day"],
            "lunar_text": lunar["text"],
        },
    )


def method3(dt: datetime) -> dict:
    """
    Lunar day (ดิถีค่ำ) + time.

    Lunar-day row cycles every 5 days:
      1,6,11 -> row 1
      2,7,12 -> row 2
      ...
      5,10,15 -> row 5

    At night, the time-column direction is reversed.
    """
    p = period_for(dt)
    lunar = thai_lunar_info(dt)

    row = (lunar["lunar_day"] - 1) % 5
    col = p.column if not p.is_night else 4 - p.column
    code = TABLE_5X5[row][col]

    return _result(
        code,
        3,
        dt,
        p,
        {
            "phase": lunar["phase"],
            "lunar_day": lunar["lunar_day"],
            "lunar_text": lunar["text"],
            "row": row + 1,
        },
    )


def all_methods(dt: datetime) -> list[dict]:
    return [method1(dt), method2(dt), method3(dt)]


def combined_score(results: list[dict]) -> dict:
    total = sum(r["score"] for r in results)
    maximum = 5 * len(results)

    if total >= 13:
        label = "ดีมาก"
        emoji = "🟢🟢"
    elif total >= 10:
        label = "ดี"
        emoji = "🟢"
    elif total >= 7:
        label = "ปานกลาง"
        emoji = "🟡"
    elif total >= 4:
        label = "ควรระวัง"
        emoji = "🟠"
    else:
        label = "ควรหลีกเลี่ยง"
        emoji = "🔴"

    return {
        "total": total,
        "maximum": maximum,
        "label": label,
        "emoji": emoji,
    }


PERIOD_STARTS = [
    (1, 13),
    (3, 37),
    (6, 1),
    (8, 25),
    (10, 49),
    (13, 13),
    (15, 37),
    (18, 1),
    (20, 25),
    (22, 49),
]


def upcoming_period_starts(after: datetime, days: int = 14):
    """
    Yield future period-start datetimes, strictly after `after`.
    """
    after = after.astimezone(BANGKOK)
    for day_offset in range(-1, days + 1):
        d = after.date() + timedelta(days=day_offset)
        for hh, mm in PERIOD_STARTS:
            candidate = _at(d, hh, mm)
            if candidate > after:
                yield candidate


def find_next_four_zero(now: datetime, method_number: int, days: int = 14) -> dict | None:
    fn: Callable[[datetime], dict] = {1: method1, 2: method2, 3: method3}[method_number]

    current = fn(now)
    if current["code"] == "four_zero":
        # User is already inside a four-zero period.
        return {
            "is_current": True,
            "result": current,
            "start": current["period"].start,
            "end": current["period"].end,
        }

    for start in upcoming_period_starts(now, days=days):
        r = fn(start)
        if r["code"] == "four_zero":
            return {
                "is_current": False,
                "result": r,
                "start": r["period"].start,
                "end": r["period"].end,
            }
    return None


def find_best_combined_period(now: datetime, days: int = 7) -> dict | None:
    """
    Search future period starts and choose the earliest period
    with the highest possible combined score found in the window.
    """
    candidates = []

    # Include current period as a candidate.
    current_results = all_methods(now)
    current_combined = combined_score(current_results)
    current_p = period_for(now)
    candidates.append({
        "start": now,
        "period_start": current_p.start,
        "period_end": current_p.end,
        "results": current_results,
        "combined": current_combined,
        "is_current": True,
    })

    for start in upcoming_period_starts(now, days=days):
        results = all_methods(start)
        candidates.append({
            "start": start,
            "period_start": period_for(start).start,
            "period_end": period_for(start).end,
            "results": results,
            "combined": combined_score(results),
            "is_current": False,
        })

    if not candidates:
        return None

    max_score = max(c["combined"]["total"] for c in candidates)
    for c in candidates:
        if c["combined"]["total"] == max_score:
            return c
    return None


def _when_text(start: datetime, end: datetime, now: datetime) -> str:
    start = start.astimezone(BANGKOK)
    end = end.astimezone(BANGKOK)
    today = now.astimezone(BANGKOK).date()

    if start.date() == today:
        day_text = "วันนี้"
    elif start.date() == today + timedelta(days=1):
        day_text = "พรุ่งนี้"
    else:
        day_text = start.strftime("%d/%m/%Y")

    return f"{day_text} {start.strftime('%H:%M')}–{end.strftime('%H:%M')}"


def format_check_now(dt: datetime | None = None) -> str:
    now = (dt or now_bangkok()).astimezone(BANGKOK)
    lunar = thai_lunar_info(now)
    results = all_methods(now)
    combined = combined_score(results)

    lines = [
        "🔮 CHECK MY LUCK NOW",
        f"📅 {now.strftime('%d/%m/%Y')}  🕒 {now.strftime('%H:%M')}",
        f"🌙 {lunar['text']}",
        f"⏱ {period_for(now).label}",
        "",
        f"① วัน + เวลา",
        f"{results[0]['emoji']} {results[0]['thai']} — {results[0]['summary']}  {results[0]['score']}/5",
        "",
        f"② ขึ้น/แรม + เวลา",
        f"{results[1]['emoji']} {results[1]['thai']} — {results[1]['summary']}  {results[1]['score']}/5",
        "",
        f"③ ดิถีค่ำ + เวลา",
        f"{results[2]['emoji']} {results[2]['thai']} — {results[2]['summary']}  {results[2]['score']}/5",
        "",
        f"📊 Combined Guidance: {combined['emoji']} {combined['label']}  {combined['total']}/{combined['maximum']}",
        "",
        "✨ NEXT สี่ศูนย์",
    ]

    for method_number in (1, 2, 3):
        found = find_next_four_zero(now, method_number)
        if not found:
            lines.append(f"Method {method_number}: ไม่พบในช่วงค้นหา")
            continue

        if found["is_current"]:
            lines.append(
                f"Method {method_number}: ✅ ตอนนี้ — ถึง {found['end'].strftime('%H:%M')}"
            )
        else:
            lines.append(
                f"Method {method_number}: {_when_text(found['start'], found['end'], now)}"
            )

    best = find_best_combined_period(now)
    if best:
        lines += [
            "",
            "🏆 BEST COMBINED PERIOD",
            _when_text(best["period_start"], best["period_end"], now),
            f"คะแนนรวม {best['combined']['total']}/{best['combined']['maximum']}",
            (
                f"M1 {best['results'][0]['score']}/5  •  "
                f"M2 {best['results'][1]['score']}/5  •  "
                f"M3 {best['results'][2]['score']}/5"
            ),
        ]

    lines += [
        "",
        "หมายเหตุ: Combined Guidance เป็นคะแนนสรุปของแอปเพื่อให้อ่านง่าย",
        "ยามอุบากองเป็นความเชื่อโบราณ โปรดใช้ประกอบการตัดสินใจ",
    ]

    return "\n".join(lines)
