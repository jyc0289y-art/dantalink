"""Layer B — 의미(Semantic) 카테고리 매칭.

트리거 이벤트의 키워드/카테고리 정보를 활용해, 종목명에 해당 키워드 또는
의미적 연관어가 포함된 KRX 종목을 후보로 제안한다.

대표 사례: "WHO 분디부교 PHEIC 선포" (HEALTH, kw=[에볼라, 백신, 분디부교])
           → 종목명에 "백신" 포함된 모든 종목 (차백신연구소, 유바이오로직스 등)
근거: 방법론.md §2.3 의미적 점화(Semantic Priming), 카테고리 매핑(아이진 사례).

신뢰도:
  - 카테고리만 매칭: 0.40 (BASE)
  - 키워드 + 종목명 substring 직접 매칭: 0.50 (강함)
"""
from __future__ import annotations

from typing import Optional

from ..models import EventCategory, TriggerEvent
from .base import BaseMatcher
from .korean_stocks import KRXStockDB
from .models import MatchCandidate


# 카테고리 → 종목명에 포함될 만한 의미적 연관어 (테마/섹터 키워드)
# 단순 substring 매칭 기반. KRX 공식 섹터 분류는 추후 통합.
_CATEGORY_THEME_KEYWORDS: dict[EventCategory, list[str]] = {
    EventCategory.HEALTH: [
        "바이오", "제약", "백신", "진단", "메디", "팜", "셀", "헬스",
        "한미", "녹십자", "셀트리온",
    ],
    EventCategory.TECH: [
        "반도체", "소프트", "테크", "솔루션", "정보", "시스템", "전자",
        "디지털", "네트워크",
    ],
    EventCategory.GEOPOLITICAL: [
        "방산", "항공우주", "에어로", "조선",
    ],
    EventCategory.DISASTER: [
        "건설", "보험", "복구",
    ],
    EventCategory.REGULATORY: [
        "증권", "금융", "은행", "보험", "캐피탈",
    ],
    EventCategory.PERSON: [
        # PERSON 자체는 Layer A 음운 매칭이 주력. 비워두고 키워드만 활용.
    ],
}

# 점수
_SCORE_THEME_ONLY = 0.40         # 카테고리 → 테마 키워드만 매칭
_SCORE_KEYWORD_SUBSTRING = 0.50  # 이벤트 키워드가 종목명에 substring으로 직접 일치

# 영문 짧은 키워드(AI, 5G 등)는 종목명 substring 매칭이 부정확 → 한국어만 사용
_MIN_KW_LENGTH = 2


def _is_korean(text: str) -> bool:
    """한글 포함 여부."""
    return any("가" <= c <= "힣" for c in text)


class SemanticMatcher(BaseMatcher):
    """Layer B — 카테고리·키워드 기반 의미 매칭."""

    name = "SemanticMatcher"
    layer = "semantic"

    def __init__(
        self,
        stock_db: KRXStockDB,
        min_marcap_eok: int = 100,
        max_marcap_eok: Optional[int] = None,
        max_per_keyword: int = 8,
        name: Optional[str] = None,
    ):
        super().__init__(name=name)
        self.db = stock_db
        self.min_marcap_eok = min_marcap_eok
        self.max_marcap_eok = max_marcap_eok
        self.max_per_keyword = max_per_keyword

    def match(self, event: TriggerEvent) -> list[MatchCandidate]:
        seen_codes: set[str] = set()
        candidates: list[MatchCandidate] = []

        # 1) 이벤트 키워드 → 종목명 substring 직접 매칭 (강한 신호)
        for kw in event.keywords:
            if not _is_korean(kw) or len(kw) < _MIN_KW_LENGTH:
                continue
            stocks = self.db.find_by_substring(kw)
            stocks_sorted = sorted(
                stocks,
                key=lambda s: s.marcap_eok or 0,
                reverse=True,
            )
            picked = 0
            for s in stocks_sorted:
                if s.code in seen_codes:
                    continue
                if s.marcap_eok < self.min_marcap_eok:
                    continue
                if self.max_marcap_eok is not None and s.marcap_eok > self.max_marcap_eok:
                    continue
                seen_codes.add(s.code)
                candidates.append(MatchCandidate(
                    stock_code=s.code,
                    stock_name=s.name,
                    market=s.market,
                    marcap_eok=s.marcap_eok,
                    trigger_event_id=event.event_id,
                    layer=self.layer,
                    score=_SCORE_KEYWORD_SUBSTRING,
                    matched_on=kw,
                    reason=(
                        f"이벤트 키워드 '{kw}'가 종목명 '{s.name}'에 직접 포함됨"
                    ),
                    details={
                        "match_kind": "keyword_substring",
                        "category": event.category.value,
                    },
                ))
                picked += 1
                if picked >= self.max_per_keyword:
                    break

        # 2) 카테고리 → 테마 키워드 → 종목명 substring 매칭 (약한 신호)
        theme_keywords = _CATEGORY_THEME_KEYWORDS.get(event.category, [])
        for theme in theme_keywords:
            stocks = self.db.find_by_substring(theme)
            stocks_sorted = sorted(
                stocks,
                key=lambda s: s.marcap_eok or 0,
                reverse=True,
            )
            picked = 0
            for s in stocks_sorted:
                if s.code in seen_codes:
                    continue
                if s.marcap_eok < self.min_marcap_eok:
                    continue
                if self.max_marcap_eok is not None and s.marcap_eok > self.max_marcap_eok:
                    continue
                seen_codes.add(s.code)
                candidates.append(MatchCandidate(
                    stock_code=s.code,
                    stock_name=s.name,
                    market=s.market,
                    marcap_eok=s.marcap_eok,
                    trigger_event_id=event.event_id,
                    layer=self.layer,
                    score=_SCORE_THEME_ONLY,
                    matched_on=theme,
                    reason=(
                        f"이벤트 카테고리 '{event.category.value}'의 테마 키워드 "
                        f"'{theme}'가 종목명 '{s.name}'에 포함됨"
                    ),
                    details={
                        "match_kind": "category_theme",
                        "category": event.category.value,
                    },
                ))
                picked += 1
                if picked >= self.max_per_keyword:
                    break

        return candidates
