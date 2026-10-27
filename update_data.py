"""Fetch market data and write site/data.json for the dashboard.

Indexes, market breadth (new highs/lows, advance/decline, Weinstein stages)
over the S&P 1500 in tickers.csv, and a theme tracker built from ETFs.
"""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).parent
OUT = ROOT / "site" / "data.json"

INDEXES = ["SPY", "QQQ", "IWM"]

# Theme name -> ETF used as its proxy
THEMES = {
    "Cybersecurity": "CIBR",
    "Semiconductors": "SMH",
    "Aerospace": "ITA",
    "Quantum": "QTUM",
    "Industrials": "XLI",
    "Oil & Gas": "XOP",
    "Telecom": "IYZ",
    "Airlines": "JETS",
    "Genomics": "ARKG",
    "AI": "AIQ",
    "Gold Miners": "GDX",
    "Silver Miners": "SIL",
    "Software": "IGV",
    "Transports": "IYT",
    "Real Estate": "VNQ",
    "Biotechnology": "IBB",
    "Banks": "KBE",
    "Robotics": "BOTZ",
    "China Internet": "KWEB",
    "Medical": "IHI",
    "Materials": "XLB",
    "HealthCare": "XLV",
    "Utilities": "XLU",
    "Steel": "SLX",
    "Retail": "XRT",
    "Growth Stocks": "ARKK",
    "Bitcoin Miners": "WGMI",
    "Solar": "TAN",
    "Home Construction": "ITB",
    "Social Media": "SOCL",
    "Bitcoin": "IBIT",
}

# Weinstein stage rules on the 150-day (30-week) average.
# The MA counts as rising/falling when it moved more than FLAT_PCT over SLOPE_DAYS.
MA_LEN = 150
SLOPE_DAYS = 20
FLAT_PCT = 1.0


def num(x, nd=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    return round(float(x), nd)


def pct(a, b):
    if b is None or a is None or b == 0 or pd.isna(a) or pd.isna(b):
        return None
    return num((a / b - 1) * 100)


def download(tickers, period):
    df = yf.download(tickers, period=period, interval="1d", auto_adjust=True,
                     group_by="column", threads=True, progress=False)
    return df


def index_cards():
    data = download(INDEXES, "10d")
    close = data["Close"]
    cards = []
    for t in INDEXES:
        s = close[t].dropna()
        last, prev = s.iloc[-1], s.iloc[-2]
        card = {"ticker": t, "price": num(last), "change": num(last - prev),
                "changePct": pct(last, prev), "extPct": None, "extLabel": None}
        try:
            info = yf.Ticker(t).info
            for key, label in (("postMarketChangePercent", "post"), ("preMarketChangePercent", "pre")):
                if info.get(key) is not None:
                    card["extPct"] = num(info[key])
                    card["extLabel"] = label
                    break
        except Exception:
            pass
        cards.append(card)
    return cards


def theme_tracker():
    tickers = list(THEMES.values())
    close = download(tickers, "15mo")["Close"]
    year_start = pd.Timestamp(datetime.now().year, 1, 1)
    rows = []
    for name, t in THEMES.items():
        s = close[t].dropna() if t in close else pd.Series(dtype=float)
        if len(s) < 2:
            continue
        last = s.iloc[-1]
        before_year = s[s.index < year_start]
        rows.append({
            "name": name,
            "ticker": t,
            "today": pct(last, s.iloc[-2]),
            "1w": pct(last, s.iloc[-6]) if len(s) > 5 else None,
            "1m": pct(last, s.iloc[-22]) if len(s) > 21 else None,
            "ytd": pct(last, before_year.iloc[-1]) if len(before_year) else None,
        })
    return rows


def stage_of(close, ma):
    """Classify one stock into Weinstein stage 1-4, or None without enough history."""
    ma = ma.dropna()
    if len(ma) <= SLOPE_DAYS:
        return None
    price, now, then = close.iloc[-1], ma.iloc[-1], ma.iloc[-1 - SLOPE_DAYS]
    slope = (now / then - 1) * 100
    above = price > now
    if above and slope > FLAT_PCT:
        return 2
    if not above and slope < -FLAT_PCT:
        return 4
    if above:
        return 1   # price above a flat/falling MA: basing or early turn
    return 3       # price below a flat/rising MA: topping


def breadth():
    universe = pd.read_csv(ROOT / "tickers.csv")["ticker"].tolist()
    data = download(universe, "14mo")
    close, high, low = data["Close"], data["High"], data["Low"]

    highs = lows = adv = dec = 0
    stages = {1: 0, 2: 0, 3: 0, 4: 0}
    above50 = above200 = counted = 0
    stage2 = []

    for t in universe:
        if t not in close:
            continue
        c = close[t].dropna()
        if len(c) < 30:
            continue
        h, l = high[t].dropna(), low[t].dropna()
        counted += 1

        if c.iloc[-1] > c.iloc[-2]:
            adv += 1
        elif c.iloc[-1] < c.iloc[-2]:
            dec += 1

        window_h, window_l = h.iloc[-252:], l.iloc[-252:]
        if h.iloc[-1] >= window_h.max():
            highs += 1
        if l.iloc[-1] <= window_l.min():
            lows += 1

        ma50 = c.rolling(50).mean()
        ma200 = c.rolling(200).mean()
        if not pd.isna(ma50.iloc[-1]) and c.iloc[-1] > ma50.iloc[-1]:
            above50 += 1
        if not pd.isna(ma200.iloc[-1]) and c.iloc[-1] > ma200.iloc[-1]:
            above200 += 1

        st = stage_of(c, c.rolling(MA_LEN).mean())
        if st:
            stages[st] += 1
            # Stage 2 names closing at a 52-week high: candidate leaders
            if st == 2 and h.iloc[-1] >= window_h.max():
                stage2.append({"ticker": t, "price": num(c.iloc[-1]),
                               "changePct": pct(c.iloc[-1], c.iloc[-2])})

    staged = sum(stages.values()) or 1
    return {
        "universe": "S&P 1500",
        "counted": counted,
        "newHighs": highs,
        "newLows": lows,
        "advance": adv,
        "decline": dec,
        "above50Pct": num(above50 / counted * 100, 0) if counted else None,
        "above200Pct": num(above200 / counted * 100, 0) if counted else None,
        "stages": [{"stage": k, "count": v, "pct": num(v / staged * 100, 0)} for k, v in stages.items()],
        "leaders": sorted(stage2, key=lambda r: -(r["changePct"] or 0))[:20],
    }


def main():
    out = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "indexes": index_cards(),
        "breadth": breadth(),
        "themes": theme_tracker(),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT} ({out['breadth']['counted']} stocks, {len(out['themes'])} themes)")


if __name__ == "__main__":
    main()
