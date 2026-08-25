# -*- coding: utf-8 -*-
"""텔레그램 공개 채널의 웹 미리보기(t.me/s/채널)를 읽어온다.
로그인도 API 키도 필요 없다. 공개 미리보기가 켜진 채널만 된다."""
import json, os, re, html, urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "telegram.json")

UA = "Mozilla/5.0 (compatible; MarketOverviewBot/1.0)"

# (표시이름, 채널아이디, 설명)  — 2026-08-25 에 미리보기 동작 확인함
CHANNELS = [
    ("Tree News",      "treenewsfeed",         "초속보 헤드라인"),
    ("BWEnews",        "BWEnews",              "거래소 상장 공지"),
    ("FinancialJuice", "financialjuice",       "거시 지표 속보"),
    ("Wu Blockchain",  "wublockchainenglish",  "아시아 크립토"),
    ("블록미디어",      "blockmedia",           "국내 크립토"),
]

MSG_RE = re.compile(
    r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
TIME_RE = re.compile(r'<time datetime="([^"]+)"')
POST_RE = re.compile(r'data-post="([^"]+)"')
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s):
    s = s.replace("<br/>", "\n").replace("<br>", "\n")
    s = TAG_RE.sub("", s)
    return html.unescape(s).strip()


def fetch(channel, timeout=25):
    url = "https://t.me/s/%s" % channel
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def parse(page, channel):
    """메시지 블록 단위로 잘라 본문·시각·링크를 뽑는다."""
    out = []
    blocks = page.split('class="tgme_widget_message_wrap')
    for b in blocks[1:]:
        m = MSG_RE.search(b)
        if not m:
            continue
        text = strip_tags(m.group(1))
        if not text:
            continue
        t = TIME_RE.search(b)
        dt = None
        if t:
            try:
                dt = datetime.fromisoformat(t.group(1).replace("Z", "+00:00"))
            except ValueError:
                dt = None
        p = POST_RE.search(b)
        out.append({
            "text": text[:600],
            "dt": dt.astimezone(timezone.utc).isoformat() if dt else None,
            "url": "https://t.me/%s" % p.group(1) if p else "https://t.me/s/%s" % channel,
        })
    return out


def collect(limit_per_channel=12):
    items = []
    for name, cid, note in CHANNELS:
        try:
            msgs = parse(fetch(cid), cid)
        except Exception as e:
            print("  x %-16s 실패: %s" % (name, e))
            continue
        msgs = msgs[-limit_per_channel:]          # 페이지 끝이 최신
        for m in msgs:
            m["source"] = name
            m["note"] = note
        items.extend(msgs)
        print("  o %-16s %d건" % (name, len(msgs)))
    items.sort(key=lambda x: x["dt"] or "", reverse=True)
    return items


def ago(iso):
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return ""
    m = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    if m < 1:
        return "방금"
    if m < 60:
        return "%d분 전" % m
    if m < 1440:
        return "%d시간 전" % (m // 60)
    return "%d일 전" % (m // 1440)


def main():
    items = collect()[:60]
    for it in items:
        it["ago"] = ago(it["dt"])
    data = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST"),
        "channels": [{"name": n, "id": c, "note": d} for n, c, d in CHANNELS],
        "items": items,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("완료: %s  %d건" % (OUT, len(items)))
    return 0 if items else 1


if __name__ == "__main__":
    raise SystemExit(main())
