# -*- coding: utf-8 -*-
"""Gemini 무료 티어 호출기.
모델 이름이 바뀌어도 죽지 않도록 후보를 순서대로 시도합니다."""
import json, os, time, urllib.request, urllib.error

BASE = "https://generativelanguage.googleapis.com/v1beta/models"
CANDIDATES = [
    os.environ.get("GEMINI_MODEL", "").strip(),
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]
_working = None


def _post(model, key, payload, timeout=120):
    url = "%s/%s:generateContent?key=%s" % (BASE, model, key)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ask_json(prompt, key, retries=3):
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
    models = [_working] if _working else [m for m in CANDIDATES if m]
    for model in models:
        for attempt in range(retries):
            try:
                res = _post(model, key, payload)
                txt = res["candidates"][0]["content"]["parts"][0]["text"]
                out = json.loads(txt)
                _working = model
                return out
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:300]
                if e.code == 429:                       # 분당 한도 -> 기다렸다 재시도
                    time.sleep(20 * (attempt + 1))
                    continue
                if e.code in (400, 404):                # 모델 이름이 틀림 -> 다음 후보
                    print("  ! %s 사용 불가 (%s) %s" % (model, e.code, body))
                    break
                print("  ! HTTP %s %s" % (e.code, body))
                time.sleep(5)
            except Exception as e:
                print("  ! %s" % e)
                time.sleep(5)
    if _working is None:
        print("  !! 쓸 수 있는 Gemini 모델을 못 찾았습니다. GEMINI_MODEL 을 지정해 보세요.")
    return None
