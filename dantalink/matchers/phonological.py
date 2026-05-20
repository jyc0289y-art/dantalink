"""Layer A — 음운(Phonological) 매칭.

트리거 이벤트의 헤드라인·본문에서 한국어 토큰을 추출하여,
각 토큰의 첫 1~2 음절이 일치하는 KRX 종목을 후보로 제안한다.

대표 사례: "Sam Altman 방한" (한국어 표기 "샘 알트먼") → "샘" → 샘표
근거: 방법론.md §2.3 음운적 점화(Phonological Priming),
      Rashes(2001) 이름 유사성 효과.

신뢰도 (방법론.md §4 Stage 4):
  - 첫 음절만 일치: 0.30 (BASE)
  - 첫 2음절 일치: 0.40 (강한 신호)
  - 종목명과 토큰이 정확 일치: 0.55 (음운+의미 동시)
"""
from __future__ import annotations

import re
from typing import Optional

from ..models import TriggerEvent
from .base import BaseMatcher
from .korean_stocks import KRXStockDB
from .models import MatchCandidate


# 음운 매칭에서 노이즈가 될 흔한 한국어 단어들 (false positive 차단)
_STOPWORDS_MULTI = {
    # 시간/순서
    "오늘", "어제", "내일", "이번", "지난", "최근", "올해", "작년", "내년",
    # 행동/사건
    "발표", "공개", "공시", "출시", "참가", "방한", "내한", "회담", "협력",
    "투자", "추가", "확대", "발견", "선언", "분석", "조사", "참석", "선포",
    "고조", "모색", "긴장", "충돌", "급등", "급락", "출범", "선출", "관측",
    "주장", "강조", "예상", "계획", "추진", "체결", "협상", "검토", "검찰",
    "지지", "반대", "수상", "포착", "발생",
    # 기관/표기
    "정부", "관련", "기준", "예상", "전망", "보고", "성장", "감소", "기업과",
    "한국", "국내", "해외", "글로벌",
    # 보조 단어
    "통해", "위해", "대해", "따른", "또한", "이번", "하지만",
    "주식", "종목", "상장", "공급", "관심", "전망", "확정",
}

# 1자 토큰 stopword (외국인명 first 음절은 매우 적으므로 흔한 1자 음절 차단)
_STOPWORDS_SINGLE = {
    "이", "그", "저", "또", "다", "두", "세", "네", "큰", "작",
    "전", "후", "초", "말", "신", "구",  # 시간·서수
    "고", "더", "덜", "약", "약", "왜", "그", "뭐",
    "수", "년", "월", "일", "시", "분",  # 단위
}

# 음운 매칭 점수
_SCORE_FIRST_SYLLABLE_ONLY = 0.30
_SCORE_FIRST_TWO_SYLLABLES = 0.40
_SCORE_EXACT_MATCH = 0.55
# 1자 토큰은 시그널이 약하므로 점수 감점 (×0.7)
_SINGLE_TOKEN_PENALTY = 0.7


class PhonologicalMatcher(BaseMatcher):
    """Layer A — 첫 음절 일치 기반 음운 매칭.

    Args:
        stock_db: 사전 로드된 KRX 종목 DB.
        min_marcap_eok: 후보로 제안할 최소 시가총액(억원). 기본 100.
                       방법론.md §4 Stage 3: "시가총액 5,000억 이하 우선"이지만
                       Layer A는 더 보수적으로 1억 미만은 제외.
        max_per_token: 단일 토큰당 최대 후보 수 (기본 5). 흔한 첫 음절(예: "삼",
                      "한")의 폭주 방지.
    """

    name = "PhonologicalMatcher"
    layer = "phonological"

    def __init__(
        self,
        stock_db: KRXStockDB,
        min_marcap_eok: int = 100,
        max_marcap_eok: Optional[int] = None,
        max_per_token: int = 5,
        name: Optional[str] = None,
    ):
        super().__init__(name=name)
        self.db = stock_db
        self.min_marcap_eok = min_marcap_eok
        self.max_marcap_eok = max_marcap_eok  # None이면 상한 없음
        self.max_per_token = max_per_token

    def match(self, event: TriggerEvent) -> list[MatchCandidate]:
        # 1) 한국어 토큰 후보 (1~5음절 단위 — 1자는 "샘 알트먼"같은 외국인명 첫음절 포착)
        text = event.title or ""
        tokens = re.findall(r"[가-힣]{1,5}", text)

        # 중복 첫 음절 제거 + stopword 필터
        seen_first: set[str] = set()
        unique_tokens: list[str] = []
        for tok in tokens:
            if len(tok) == 1:
                if tok in _STOPWORDS_SINGLE:
                    continue
            else:
                if tok in _STOPWORDS_MULTI:
                    continue
            if tok[0] in seen_first:
                continue
            seen_first.add(tok[0])
            unique_tokens.append(tok)

        candidates: list[MatchCandidate] = []
        for token in unique_tokens:
            stocks = self.db.find_by_first_syllable(token[0])
            # 1차 필터: 시총 범위 + 점수 계산
            scored: list[tuple[float, str, object]] = []
            for s in stocks:
                if s.marcap_eok < self.min_marcap_eok:
                    continue
                if self.max_marcap_eok is not None and s.marcap_eok > self.max_marcap_eok:
                    continue
                raw_score, kind = self._score(token, s.name)
                if raw_score == 0:
                    continue
                final_score = raw_score
                if len(token) == 1:
                    final_score *= _SINGLE_TOKEN_PENALTY
                scored.append((final_score, kind, s))

            # 정렬: 점수 내림차순, 동점이면 시총 큰 종목 우선 (가독성)
            # exact > first2 > first1 자동 순. 아이진(exact 0.55)이 아이센스(first2 0.40)보다 우선.
            scored.sort(key=lambda x: (x[0], x[2].marcap_eok or 0), reverse=True)

            picked = 0
            for final_score, kind, s in scored:
                candidates.append(MatchCandidate(
                    stock_code=s.code,
                    stock_name=s.name,
                    market=s.market,
                    marcap_eok=s.marcap_eok,
                    trigger_event_id=event.event_id,
                    layer=self.layer,
                    score=final_score,
                    matched_on=token,
                    reason=(
                        f"트리거 토큰 '{token}'의 첫 음절 '{token[0]}'이 "
                        f"종목명 '{s.name}'의 첫 음절과 일치 ({kind})"
                    ),
                    details={
                        "token": token,
                        "first_syllable": token[0],
                        "match_kind": kind,
                    },
                ))
                picked += 1
                if picked >= self.max_per_token:
                    break

        return candidates

    @staticmethod
    def _score(token: str, stock_name: str) -> tuple[float, str]:
        """음운 매칭 점수 계산."""
        if not token or not stock_name:
            return 0.0, "none"
        # 정확 일치
        if token == stock_name:
            return _SCORE_EXACT_MATCH, "exact"
        # 첫 2음절 일치 (양쪽 모두 2음절 이상)
        if (len(token) >= 2 and len(stock_name) >= 2
                and token[0] == stock_name[0]
                and token[1] == stock_name[1]):
            return _SCORE_FIRST_TWO_SYLLABLES, "first2"
        # 첫 음절만 일치
        if token[0] == stock_name[0]:
            return _SCORE_FIRST_SYLLABLE_ONLY, "first1"
        return 0.0, "none"
