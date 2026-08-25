# -*- coding: utf-8 -*-
"""지수·금·은을 모아 data/market.json 으로 저장.
브라우저에서 직접 부르면 CORS 에 막히는 곳들이라 로봇이 대신 가져온다.

소스를 두 곳 준비해 순서대로 시도한다. 한 곳이 막혀도 화면이 비지 않게.
실패하면 응답 앞부분을 로그에 남겨 다음에 원인을 알 수 있게 한다.
"""
import json, os, urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "market.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 이름, 야후심볼, stooq심볼, 아이콘, 소수점, 접두, 접미
TARGETS = [
    ("S&P 500", "%5EGSPC", "^spx",    "🇺🇸", 0, "",  ""),
    ("NASDAQ",  "%5EIXIC", "^ndq",    "🇺🇸", 0, "",  ""),
    ("KOSPI",   "%5EKS11", "^kospi",  "🇰🇷", 2, "",  ""),
    ("KOSDAQ",  "%5EKQ11", "^kosdaq", "🇰🇷", 2, "",  ""),
    ("Gold",    "GC=F",    "xauusd",  "🥇", 2, "$", "/oz"),
    ("Silver",  "SI=F",    "xagusd",  "🥈", 2, "$", "/oz"),
    ("USD/KRW", "KRW=X",   "usdkrw",  "💱", 2, "₩", ""),
]


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def from_yahoo(sym):
    raw = _get("https://query1.finance.yahoo.com/v8/finance/chart/"
               "%s?range=5d&interval=1d" % sym)
    d = json.loads(raw)
    meta = d["chart"]["result"][0]["meta"]
    last = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if last is None or prev is None:
        closes = [c for c in
                  d["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                  if c is not None]
        if len(closes) < 2:
            raise ValueError("종가 부족")
        last, prev = closes[-1], closes[-2]
    return float(last), float(prev)


def from_stooq(sym):
    raw = _get("https://stooq.com/q/d/l/?s=%s&i=d" % sym)
    rows = [r for r in raw.strip().splitlines() if r.count(",") >= 5]
    if len(rows) < 3:
        raise ValueError("CSV 아님: %r" % raw[:120])
    def close(line):
        return float(line.split(",")[4])
    return close(rows[-1]), close(rows[-2])


SOURCES = [("yahoo", from_yahoo, 1), ("stooq", from_stooq, 2)]


def main():
    items = []
    for name, ysym, ssym, icon, dp, pre, suf in TARGETS:
        price = prev = None
        used = None
        for label, fn, idx in SOURCES:
            sym = ysym if idx == 1 else ssym
            try:
                price, prev = fn(sym)
                used = label
                break
            except Exception as e:
                print("  . %-9s %-6s 실패: %s" % (name, label, str(e)[:110]))
        if price is None:
            print("  x %-9s 모든 소스 실패" % name)
            continue
        chg = (price / prev - 1) * 100 if prev else None
        items.append({
            "name": name, "icon": icon,
            "price": round(price, dp),
            "changePct": round(chg, 2) if chg is not None else None,
            "display": "%s%s%s" % (pre, format(round(price, dp), ",.%df" % dp), suf),
            "src": used,
        })
        print("  o %-9s %-12s (%+.2f%%)  via %s"
              % (name, items[-1]["display"], chg or 0, used))

    data = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST"),
            "items": items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("완료: %s  %d개" % (OUT, len(items)))
    return 0 if items else 1


if __name__ == "__main__":
    raise SystemExit(main())
