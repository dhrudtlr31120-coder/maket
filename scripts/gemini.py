# -*- coding: utf-8 -*-
"""Gemini 호출기.

구글이 모델을 자주 갈아치운다. 2026-08 에 gemini-2.5-flash 가 신규 사용자에게
막히면서 "gemini-3.6-flash 를 쓰라"는 404 를 뱉었다.
그래서 이 파일은 두 가지로 대비한다.
  1) 후보 모델을 순서대로 시도한다.
  2) 404 응답 안에 대체 모델 이름이 들어 있으면 그것을 자동으로 채택한다.
"""
import json, os, re, time, urllib.request, urllib.error

BASE = "https://generativelanguage.googleapis.com/v1beta/models"
CANDIDATES = [
    os.environ.get("GEMINI_MODEL", "").strip(),
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-3.6-flash-lite",
    "gemini-2.5-flash",
]
SUGGEST_RE = re.compile(r"models/([A-Za-z0-9._-]+)")
_working = None


def _post(model, key, payload, timeout=180):
    url = "%s/%s:generateContent?key=%s" % (BASE, model, key)
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _suggested(body, tried):
    """404 본문에서 '이 모델을 쓰라'는 이름을 뽑아낸다."""
    for name in SUGGEST_RE.findall(body or ""):
        if name not in tried and "flash" in name.lower():
            return name
    return None


def ask_json(prompt, key):
    """JSON 하나를 돌려받는다. 실패하면 None."""
    global _working
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "maxOutputTokens": 8192,
        },
    }

    queue = [_working] if _working else [m for m in CANDIDATES if m]
    tried = set()

    while queue:
        model = queue.pop(0)
        if model in tried:
            continue
        tried.add(model)

        for attempt in range(3):
            try:
                res = _post(model, key, payload)
                txt = res["candidates"][0]["content"]["parts"][0]["text"]
                out = json.loads(txt)
                if _working != model:
                    print("  * 사용 모델: %s" % model)
                _working = model
                return out

            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")
                if e.code == 429:                       # 분당 한도
                    wait = 20 * (attempt + 1)
                    print("  . 한도 대기 %ds (%s)" % (wait, model))
                    time.sleep(wait)
                    continue
                if e.code == 503:                       # 모델 혼잡 - 한 번만 더
                    if attempt == 0:
                        print("  . %s 혼잡, 15초 뒤 재시도" % model)
                        time.sleep(15)
                        continue
                    print("  ! %s 혼잡이 계속됨, 다음 모델로" % model)
                    break
                if e.code in (400, 404):                # 모델이 없거나 막힘
                    alt = _suggested(body, tried)
                    print("  ! %s 사용 불가 (%s)%s"
                          % (model, e.code, " -> %s 로 전환" % alt if alt else ""))
                    if alt:
                        queue.insert(0, alt)
                    break
                print("  ! HTTP %s %s" % (e.code, body[:200]))
                time.sleep(5)

            except Exception as e:
                print("  ! %s" % e)
                time.sleep(5)

    if _working is None:
        print("  !! 쓸 수 있는 Gemini 모델이 없습니다. "
              "워크플로에 GEMINI_MODEL 환경변수로 직접 지정해 보세요.")
    return None
