"""Stage 02 데이터 모델 — MatchCandidate.

Stage 01의 TriggerEvent → Stage 02 매칭 → MatchCandidate.
신뢰도 점수(score)는 향후 Stage 03(진입 신호 검증)에서 추가 가중치.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MatchCandidate:
    """이벤트→종목 매칭 후보.

    Attributes:
        stock_code: KRX 종목코드 (6자리, 예 "071950").
        stock_name: 종목명 (예 "코아스").
        market: KOSPI / KOSDAQ / KONEX / KOSDAQ GLOBAL.
        marcap_eok: 시가총액 (억원).
        trigger_event_id: 어느 이벤트에서 매칭됐는지.
        layer: 매칭 레이어 — "phonological" / "semantic" / "weak_tie".
        score: 매칭 신뢰도 (0.0~1.0).
        matched_on: 매칭 단서 (음절·키워드).
        reason: 매칭 근거 텍스트 (사람이 읽기 위한 설명).
        details: 추가 메타데이터 (디버깅/시각화용).
    """
    stock_code: str
    stock_name: str
    market: str
    marcap_eok: int
    trigger_event_id: str
    layer: str
    score: float
    matched_on: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
