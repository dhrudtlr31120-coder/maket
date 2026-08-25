# -*- coding: utf-8 -*-
"""지수·금·은을 모아 data/market.json 으로 저장.
브라우저에서 직접 부르면 CORS 에 막히는 곳들이라 로봇이 대신 가져온다."""
import json, os, urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "market.json")
UA = "Mozilla/5.0 (compatible; MarketOverviewBot/1.0)"

# stooq 심볼: 이름, 심볼, 아이콘, 소수점
TARGETS = [
    ("S&P 500", "^spx",   "🇺🇸", 0),
    ("NASDAQ",  "^ndq",   "🇺🇸", 0),
    ("KOSPI",   "^kospi", "🇰🇷", 2),
    ("KOSDAQ",  "^kosdaq","🇰🇷", 2),
    ("Gold",    "xauusd", "🥇", 2),
    ("Silver",  "xagusd", "🥈", 2),
    ("USD/KRW", "usdkrw", "💱", 2),
]


def stooq(symbol, timeout=20):
    """일봉 2개를 받아 종가와 전일 대비 변동률을 계산한다."""
    url = "https://stooq.com/q/d/l/?s=%s&i=d" % symbol
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        rows = r.read().decode("utf-8", "replace").strip().splitlines()
    if len(rows) < 3:
        raise ValueError("데이터 부족")
    def close(line):
        return float(line.split(",")[4])
    last, prev = close(rows[-1]), close(rows[-2])
    return last, (last / prev - 1) * 100 if prev else None


def main():
    items = []
    for name, sym, icon, dp in TARGETS:
        try:
            price, chg = stooq(sym)
        except Exception as e:
            print("  x %-9s %s" % (name, e))
            continue
        prefix = "₩" if sym == "usdkrw" else ("$" if sym.startswith("xa") else "")
        suffix = "/oz" if sym.startswith("xa") else ""
        items.append({
            "name": name, "icon": icon,
            "price": round(price, dp),
            "changePct": round(chg, 2) if chg is not None else None,
            "display": "%s%s%s" % (prefix, format(round(price, dp), ",.%df" % dp), suffix),
        })
        print("  o %-9s %s (%+.2f%%)" % (name, items[-1]["display"], chg or 0))

    data = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST"), "items": items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("완료: %s  %d개" % (OUT, len(items)))
    return 0 if items else 1


if __name__ == "__main__":
    raise SystemExit(main())
