# -*- coding: utf-8 -*-
"""수집할 RSS 목록. 여기만 고치면 됩니다.
2026-08-24 에 전부 직접 열어 살아있는 것만 남겼습니다."""

FEEDS = [
    # ---- 크립토 (해외) ----
    ("CoinDesk",              "https://www.coindesk.com/arc/outboundfeeds/rss/",      "crypto"),
    ("The Block",             "https://www.theblock.co/rss.xml",                      "crypto"),
    ("CryptoSlate",           "https://cryptoslate.com/feed/",                        "crypto"),
    ("Cointelegraph",         "https://cointelegraph.com/rss",                        "crypto"),
    ("Decrypt",               "https://decrypt.co/feed",                              "crypto"),
    # ---- 크립토 (국내) ----
    ("블록미디어",             "https://www.blockmedia.co.kr/feed",                    "crypto"),
    ("토큰포스트",             "https://www.tokenpost.kr/rss",                         "crypto"),
    # ---- 반도체 ----
    ("더일렉",                 "https://www.thelec.kr/rss/allArticle.xml",             "semi"),
    ("전자신문",               "https://rss.etnews.com/Section902.xml",                "semi"),
    ("Tom's Hardware",        "https://www.tomshardware.com/feeds/all",               "semi"),
    ("Semiconductor Eng.",    "https://semiengineering.com/feed/",                    "semi"),
    # ---- 금·은·원자재 ----
    ("FXStreet",              "https://www.fxstreet.com/rss/news",                    "metal"),
    ("MINING.COM",            "https://www.mining.com/feed/",                         "metal"),
    ("Investing 원자재",       "https://www.investing.com/rss/news_11.rss",            "metal"),
    # ---- 거시·시장 ----
    ("한국경제",               "https://www.hankyung.com/feed/finance",                "macro"),
    ("MarketWatch",           "https://feeds.content.dowjones.io/public/rss/mw_bulletins", "macro"),
    ("Yahoo Finance",         "https://finance.yahoo.com/news/rssindex",              "macro"),
]

# 요약 카드 3장을 만들 그룹
DIGESTS = [
    ("crypto", "Crypto Summary",   ["crypto"]),
    ("macro",  "경제 · 거시",        ["macro", "metal"]),
    ("semi",   "반도체 · 산업",       ["semi"]),
]
