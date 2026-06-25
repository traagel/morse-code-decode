"""Fetch Tartu (UT Physicum) weather and turn it into a Morse-safe report.

Source: https://meteo.physic.ut.ee — the archive CSV endpoint. No API key,
no extra deps (stdlib urllib).
"""

import urllib.parse
import urllib.request
from datetime import date, timedelta

_ARCHIVE = "https://meteo.physic.ut.ee/et/archive.php"
_COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Station location (UT Physicum, Tartu), decimal degrees.
STATION = (58.366449, 26.690668)


def _url(day: date) -> str:
    nxt = day + timedelta(days=1)
    params = {
        "do": "data",
        "begin[year]": day.year, "begin[mon]": day.month, "begin[mday]": day.day,
        "end[year]": nxt.year, "end[mon]": nxt.month, "end[mday]": nxt.day,
        # Column selectors: temp, humidity, pressure, wind speed/dir, precip, etc.
        "9": 1, "12": 1, "10": 1, "15": 1, "16": 1, "17": 1, "11": 1, "14": 1, "13": 1,
        "ok": " Esita päring ",
    }
    return _ARCHIVE + "?" + urllib.parse.urlencode(params)


def _fetch(day: date) -> str:
    req = urllib.request.Request(_url(day), headers={"User-Agent": "morse-cli"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", "replace")


def latest_reading(day: date | None = None) -> dict | None:
    """Most recent parsed row for ``day`` (default today), or None if empty.

    CSV columns: time, temp °C, humidity %, pressure hPa, wind m/s, wind °, precip.
    """
    rows = []
    for line in _fetch(day or date.today()).splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7 or not parts[0][:4].isdigit():
            continue  # header / blank / malformed
        try:
            rows.append(
                {
                    "time": parts[0],
                    "temp": float(parts[1]),
                    "humidity": float(parts[2]),
                    "pressure": float(parts[3]),
                    "wind": float(parts[4]),
                    "direction": float(parts[5]),
                    "precip": float(parts[6] or 0),
                }
            )
        except ValueError:
            continue
    return rows[-1] if rows else None


def _cardinal(deg: float) -> str:
    return _COMPASS[round(deg / 45) % 8]


def coordinates(lat: float | None = None, lon: float | None = None) -> str:
    """Decimal-degree position line, defaulting to the station.

    e.g. 'LAT 58.3664 N LON 26.6907 E'. ~11 m resolution, plenty for a fixed
    station and shorter to key than full precision.
    """
    lat = STATION[0] if lat is None else lat
    lon = STATION[1] if lon is None else lon
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"LAT {abs(lat):.4f} {ns} LON {abs(lon):.4f} {ew}"


def report(reading: dict) -> str:
    """One-line summary using only Morse-table chars (A-Z, 0-9, space)."""
    hhmm = reading["time"][11:16].replace(":", "")
    t = round(reading["temp"])
    parts = [
        "WX TARTU", f"{hhmm}Z",
        "TEMP", f"MINUS {abs(t)}" if t < 0 else str(t),
        "HUM", str(round(reading["humidity"])),
        "PRES", str(round(reading["pressure"])),
        "WIND", str(round(reading["wind"])), "MS", _cardinal(reading["direction"]),
    ]
    if reading["precip"] > 0:
        parts.append("RAIN")
    return " ".join(parts)


def weather_report(day: date | None = None) -> str:
    """Fetch and summarize the latest reading. Raises if no data."""
    reading = latest_reading(day)
    if reading is None:
        raise SystemExit("no weather data returned")
    return f"{report(reading)} {coordinates()}"
