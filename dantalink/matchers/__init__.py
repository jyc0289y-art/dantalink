"""DantaLink Stage 02 — 매칭 후보 생성 모듈.

행동재무 기반 인지 매칭으로 트리거 이벤트와 한국 종목을 연결한다.

Layer A — Phonological: 음운(첫 음절) 일치
Layer B — Semantic: 카테고리·테마 매핑
Layer C — Weak Tie: 약한 연결 (향후 추가)
"""
from .base import BaseMatcher
from .korean_stocks import KRXStock, KRXStockDB
from .models import MatchCandidate
from .phonological import PhonologicalMatcher
from .semantic import SemanticMatcher

__all__ = [
    "BaseMatcher",
    "KRXStock",
    "KRXStockDB",
    "MatchCandidate",
    "PhonologicalMatcher",
    "SemanticMatcher",
]
