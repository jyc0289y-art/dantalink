"""DantaLink 휴리스틱 분류기.

LLM 분류 전 단계에서 키워드 사전 기반으로 1차 카테고리 분류를 수행한다.
가장 많은 키워드가 매칭된 카테고리를 채택한다. tie-break은 사전 정의된 우선순위.
"""
from __future__ import annotations

import re
from typing import Iterable

from ..models import EventCategory


# 카테고리별 키워드 사전.
# 가중치가 필요하면 dict로 전환 가능 (key=kw, value=weight).
CATEGORY_KEYWORDS: dict[EventCategory, list[str]] = {
    EventCategory.HEALTH: [
        # 한국어
        "에볼라", "바이러스", "백신", "감염병", "팬데믹", "변종",
        "분디부교", "한타바이러스", "코로나", "독감", "임상시험",
        "WHO", "CDC", "PHEIC", "질병관리청",
        # 영어
        "ebola", "virus", "vaccine", "outbreak", "pandemic",
        "infection", "clinical trial", "FDA approval",
    ],
    EventCategory.GEOPOLITICAL: [
        # 한국어
        "전쟁", "공격", "미사일", "제재", "정상회담", "휴전",
        "이란", "북한", "러시아", "우크라이나", "중동", "이스라엘",
        "관세", "무역분쟁", "수출규제", "호르무즈",
        # 영어
        "war", "attack", "sanction", "summit", "tariff",
        "ceasefire", "missile", "invasion",
        "Iran", "North Korea", "Russia", "Ukraine", "Israel",
        "Hormuz", "tension", "tensions",
    ],
    EventCategory.TECH: [
        # 한국어
        "인공지능", "반도체", "메모리", "온디바이스",
        "양자컴퓨팅", "로보틱스", "자율주행", "전기차",
        # 영어 / 고유명사
        "OpenAI", "GPT", "Claude", "Anthropic", "Gemini",
        "AI", "HBM", "NVIDIA", "TSMC", "ASML",
        "quantum", "robotics", "autonomous",
    ],
    EventCategory.PERSON: [
        # 한국어
        "방한", "내한", "회담", "발언", "인터뷰", "기자회견",
        "취임", "사임", "임명",
        # 영어
        "visit", "speech", "interview", "press conference",
        "announce", "statement",
        # 직함은 PERSON 시그널이지만 다른 카테고리와 자주 공존하므로 약하게
        "CEO", "대통령", "총리", "장관",
    ],
    EventCategory.DISASTER: [
        "지진", "쓰나미", "화재", "폭발", "사고", "추락", "침몰",
        "산사태", "홍수", "태풍",
        "earthquake", "tsunami", "fire", "explosion", "crash",
        "flood", "typhoon", "landslide",
    ],
    EventCategory.REGULATORY: [
        "금리", "FOMC", "한은", "기준금리", "규제", "법안",
        "환율", "원달러", "달러인덱스", "물가지수", "CPI", "PPI",
        "rate", "Fed", "regulation", "bill", "policy",
        "inflation",
    ],
}

# 동점일 때 채택할 카테고리 우선순위 (위쪽일수록 우선).
# 단타 시장 관점에서 더 강한 모멘텀을 만드는 순서로 배치.
TIEBREAK_PRIORITY = [
    EventCategory.HEALTH,
    EventCategory.GEOPOLITICAL,
    EventCategory.TECH,
    EventCategory.DISASTER,
    EventCategory.REGULATORY,
    EventCategory.PERSON,
]


def classify(text: str) -> tuple[EventCategory, list[str]]:
    """텍스트를 휴리스틱 분류한다.

    Args:
        text: 분류할 문자열 (제목 + 본문 합쳐서 전달 권장).

    Returns:
        (선택된 카테고리, 매칭된 전체 키워드 목록).
        매칭 키워드가 0개이면 (UNKNOWN, []) 반환.
    """
    if not text:
        return EventCategory.UNKNOWN, []

    text_lower = text.lower()
    matches: dict[EventCategory, list[str]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        hits: list[str] = []
        for kw in keywords:
            # 영문 키워드는 word boundary 매칭, 한글은 단순 substring
            if re.match(r"^[\x00-\x7F]+$", kw):
                pattern = r"\b" + re.escape(kw.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    hits.append(kw)
            else:
                if kw in text:
                    hits.append(kw)
        if hits:
            matches[category] = hits

    if not matches:
        return EventCategory.UNKNOWN, []

    # 1차: 매칭 개수 기준
    max_count = max(len(v) for v in matches.values())
    top_candidates = [c for c, v in matches.items() if len(v) == max_count]

    # 2차: 우선순위
    for c in TIEBREAK_PRIORITY:
        if c in top_candidates:
            chosen = c
            break
    else:
        chosen = top_candidates[0]

    # 매칭된 모든 키워드 (중복 제거, 입력 순서 보존)
    all_kw: list[str] = []
    seen: set[str] = set()
    for kws in matches.values():
        for kw in kws:
            if kw not in seen:
                seen.add(kw)
                all_kw.append(kw)

    return chosen, all_kw


def matches_any_keyword(text: str, watch_keywords: Iterable[str]) -> list[str]:
    """사용자 정의 워치 키워드와 매칭되는 항목 반환.

    수집기에서 1차 필터링용으로 사용. 영문 키워드는 word boundary 매칭,
    한글 키워드는 단순 substring 매칭.
    """
    if not text:
        return []
    text_lower = text.lower()
    hit: list[str] = []
    for kw in watch_keywords:
        if re.match(r"^[\x00-\x7F]+$", kw):
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, text_lower):
                hit.append(kw)
        else:
            if kw in text:
                hit.append(kw)
    return hit
