# Market Overview

크립토 · 반도체 · 원자재 시세와 뉴스를 한 화면에 모으는 개인용 대시보드.
서버를 빌리지 않습니다. 전부 무료 티어로 돌아갑니다.

## 어떻게 돌아가나

두 갈래로 데이터가 들어옵니다.

1. **브라우저가 직접** — 코인 시세, 김프, 공포탐욕, 도미넌스
   업비트 · 바이낸스 · CoinPaprika · alternative.me 공개 API를 60초마다 호출합니다.
   서버가 필요 없고 항상 실시간입니다.

2. **로봇이 대신** — 뉴스, AI 요약, 텔레그램, 지수·금은
   GitHub Actions가 하루 4번 돌면서 결과를 `data/*.json` 으로 저장하고 커밋합니다.
   브라우저에서 직접 부르면 CORS에 막히거나 API 키가 필요한 것들입니다.

```
RSS 17곳 ─┐
텔레그램 5곳 ─┼→ GitHub Actions (하루 4회) → data/*.json → 정적 페이지
지수·금은 ─┘         └ Gemini Flash 로 호재/악재 분류 + 요약
```

## 처음 한 번만 하는 설정

1. 이 파일들을 GitHub 저장소에 올린다 (Public 이어야 무료 한도가 무제한)
2. **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `GEMINI_API_KEY`
   - Secret: https://aistudio.google.com/apikey 에서 받은 키
3. **Settings → Pages → Source: GitHub Actions**
4. **Actions 탭 → collect → Run workflow** 를 눌러 첫 수집을 돌린다
   (기다리지 않고 바로 데이터를 채우려면)

## 고치고 싶을 때

| 무엇을 | 어디를 |
|---|---|
| 뉴스 출처 추가·삭제 | `scripts/feeds.py` 의 `FEEDS` |
| 텔레그램 채널 변경 | `scripts/collect_telegram.py` 의 `CHANNELS` |
| 코인 목록 | `index.html` 상단의 `COINS` |
| 지수·금은 종목 | `scripts/collect_market.py` 의 `TARGETS` |
| 수집 주기 | `.github/workflows/collect.yml` 의 `cron` (UTC 기준) |
| 사이트 제목·닉네임 | `index.html` 의 `<title>`, `<h1>` / Settings → Variables 의 `SITE_HANDLE` |

## 알아둘 것

- **텔레그램은 공개 미리보기가 켜진 채널만** 읽힙니다. 안 되는 채널은 조용히 건너뜁니다.
  로그인도 API 키도 쓰지 않으므로 계정이 걸릴 일이 없습니다.
- **Gemini 무료 티어는 하루 약 1,500회**입니다. 이 설정은 하루 30~40회를 씁니다.
- `GEMINI_API_KEY` 가 없으면 분류·요약만 건너뛰고 나머지는 정상 동작합니다.
- 모델 이름이 바뀌어도 `scripts/gemini.py` 가 후보를 순서대로 시도합니다.
  특정 모델을 쓰려면 워크플로에 `GEMINI_MODEL` 환경변수를 추가하세요.

## 파일

```
index.html                     대시보드 (단일 파일)
data/*.json                    로봇이 채우는 데이터
scripts/feeds.py               RSS 목록
scripts/gemini.py              Gemini 호출기
scripts/collect_news.py        RSS → 분류 → 요약
scripts/collect_telegram.py    t.me/s/ 미리보기 읽기
scripts/collect_market.py      지수 · 금 · 은
.github/workflows/collect.yml  하루 4회 수집
.github/workflows/deploy.yml   main 푸시 시 Pages 배포
```
