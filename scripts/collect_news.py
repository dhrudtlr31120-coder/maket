# -*- coding: utf-8 -*-
"""RSS 를 모아 Gemini 로 호재/악재 분류 + 일일 요약 -> data/news.json"""
import json, os, re, sys, time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feedparser
from feeds import FEEDS, DIGESTS
from gemini import ask_json

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "news.json")

WINDOW_HOURS = int(os.environ.get("WINDOW_HOURS", "24"))
MAX_PER_FEED = 15
MAX_CARDS = 60
HANDLE = os.environ.get("SITE_HANDLE", "simon")


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def entry_time(e):
    for k in ("published_parsed", "updated_parsed"):
        t = getattr(e, k, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def ago(dt):
    if not dt:
        return ""
    m = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    if m < 1:
        return "방금"
    if m < 60:
        return "%d분 전" % m
    if m < 1440:
        return "%d시간 전" % (m // 60)
    return "%d일 전" % (m // 1440)


def collect():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=WINDOW_HOURS)
    items = []
    for name, url, group in FEEDS:
        try:
            d = feedparser.parse(url)
        except Exception as e:
            print("  x %-20s 실패: %s" % (name, e))
            continue
        if not getattr(d, "entries", None):
            print("  x %-20s 항목 없음" % name)
            continue
        n = 0
        for e in d.entries[:MAX_PER_FEED]:
            dt = entry_time(e)
            if dt and dt < cutoff:
                continue
            title = clean(getattr(e, "title", ""))
            if not title:
                continue
            items.append({
                "title": title[:200],
                "url": getattr(e, "link", ""),
                "source": name,
                "group": group,
                "summary": clean(getattr(e, "summary", ""))[:300],
                "dt": dt.isoformat() if dt else None,
                "ago": ago(dt),
                "_sort": dt.timestamp() if dt else 0,
            })
            n += 1
        print("  o %-20s %d건" % (name, n))
    items.sort(key=lambda x: x["_sort"], reverse=True)
    return items


CLASSIFY = u"""너는 한국 투자자를 위한 뉴스 분석가다.
아래 뉴스 목록을 각각 자산 가격에 미치는 방향으로 분류하라.

분류 기준:
- "호재": 가격을 올릴 재료 (승인, 유입, 상장, 실적 호조, 완화적 정책, 대형 투자)
- "악재": 가격을 내릴 재료 (해킹, 규제 강화, 유출, 부도, 긴축, 소송 패소)
- "모호": 방향이 불분명하거나 단순 사실 전달, 시황 요약, 의견/전망 기사

또한 투자 판단에 무의미한 잡음(광고, 이벤트 홍보, 가십, 생활 기사, 스포츠,
연예, 사건사고, 신제품 리뷰)은 tone 을 "제외" 로 표시하라.
제목을 자연스러운 한국어로 40자 이내로 다듬어 ko 에 넣어라.
영어 제목은 번역하고, 한국어 제목은 군더더기만 덜어내라.

출력은 오직 JSON: {"results":[{"i":번호,"tone":"호재|악재|모호|제외","ko":"다듬은 제목"}]}

뉴스 목록:
%s"""

DIGEST = u"""너는 한국 투자자를 위한 브리핑 작성자다.
아래 뉴스들을 읽고 "%s" 요약 카드를 만들어라.

규칙:
- 섹션 2~4개로 묶어라. 섹션 제목은 내용에 맞게 직접 지어라.
- 각 항목은 한 줄, 40자 이내, 명사형으로 끝내라 (예: "...유입 확인됨").
- 중복되는 뉴스는 하나로 합쳐라.
- 잡음(광고, 가십, 생활 기사)은 버려라.
- 마지막에 oneLine 으로 오늘의 핵심을 한 문장으로 써라.

출력은 오직 JSON:
{"sections":[{"h":"섹션 제목","items":["...","..."]}],"oneLine":"..."}

뉴스:
%s"""


def classify(items, key):
    tagged = []
    B = 25
    for s in range(0, min(len(items), 200), B):
        chunk = items[s:s + B]
        listing = "\n".join(
            "%d. [%s] %s" % (i, c["source"], c["title"]) for i, c in enumerate(chunk))
        res = ask_json(CLASSIFY % listing, key)
        if not res or "results" not in res:
            print("  ! 분류 실패, 원제목으로 대체")
            for c in chunk:
                c["tone"] = "모호"
                c["ko"] = c["title"]
                tagged.append(c)
            continue
        by_i = {r.get("i"): r for r in res["results"] if isinstance(r, dict)}
        for i, c in enumerate(chunk):
            r = by_i.get(i, {})
            c["tone"] = r.get("tone", "모호")
            c["ko"] = (r.get("ko") or c["title"])[:120]
            tagged.append(c)
        time.sleep(5)          # 무료 티어 분당 한도 여유
    return tagged


def build_digests(items, key):
    out = []
    for dkey, title, groups in DIGESTS:
        pool = [c for c in items if c["group"] in groups and c.get("tone") != "제외"][:45]
        if not pool:
            continue
        listing = "\n".join("- [%s] %s" % (c["source"], c.get("ko") or c["title"]) for c in pool)
        res = ask_json(DIGEST % (title, listing), key)
        if not res:
            continue
        srcs = sorted(set(c["source"] for c in pool))
        out.append({
            "key": dkey,
            "title": title,
            "date": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
            "sections": res.get("sections", []),
            "oneLine": res.get("oneLine", ""),
            "sources": srcs,
        })
        time.sleep(5)
    return out


def main():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    print("[1/3] RSS 수집")
    items = collect()
    print("  -> 총 %d건" % len(items))
    if not items:
        print("수집된 뉴스가 없습니다. 종료.")
        return 1

    if key:
        print("[2/3] Gemini 분류")
        items = classify(items, key)
        print("[3/3] Gemini 요약")
        digests = build_digests(items, key)
    else:
        print("!! GEMINI_API_KEY 없음 - 분류/요약을 건너뜁니다")
        for c in items:
            c["tone"] = "모호"
            c["ko"] = c["title"]
        digests = []

    cards = [{
        "tone": c["tone"], "title": c.get("ko") or c["title"],
        "url": c["url"], "source": c["source"], "ago": c["ago"], "group": c["group"],
    } for c in items if c.get("tone") in ("호재", "악재", "모호")][:MAX_CARDS]

    data = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST"),
        "handle": HANDLE,
        "counts": {
            "호재": sum(1 for c in cards if c["tone"] == "호재"),
            "악재": sum(1 for c in cards if c["tone"] == "악재"),
            "모호": sum(1 for c in cards if c["tone"] == "모호"),
            "제외": sum(1 for c in items if c.get("tone") == "제외"),
        },
        "cards": cards,
        "digests": digests,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("완료: %s  카드 %d장, 요약 %d개  %s"
          % (OUT, len(cards), len(digests), data["counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
