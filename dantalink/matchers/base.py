"""BaseMatcher — 매칭 레이어 공통 추상 베이스.

모든 매칭 레이어(phonological, semantic, weak_tie)는 이 클래스를 상속받아
일관된 인터페이스로 TriggerEvent → list[MatchCandidate] 변환을 수행한다.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from ..models import TriggerEvent
from .models import MatchCandidate


class BaseMatcher(ABC):
    """모든 매칭 레이어의 추상 베이스.

    구현 클래스는 다음을 정의해야 한다:
      - name: 매칭기 이름 (로깅용)
      - layer: 매칭 레이어 식별자 ("phonological" 등)
      - match(): 단일 이벤트 → 후보 리스트
    """

    name: str
    layer: str

    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"dantalink.{self.name}")

    @abstractmethod
    def match(self, event: TriggerEvent) -> list[MatchCandidate]:
        """이벤트에서 매칭 후보 리스트 추출.

        예외는 매칭기 내부에서 처리하고 빈 리스트 반환 권장.
        """
        ...

    def safe_match(self, event: TriggerEvent) -> list[MatchCandidate]:
        """try/except로 감싼 안전 버전."""
        try:
            candidates = self.match(event)
            self.logger.debug(
                f"{self.name} → event {event.event_id[:8]}: {len(candidates)}건"
            )
            return candidates
        except Exception as e:
            self.logger.exception(f"{self.name} 매칭 중 오류: {e}")
            return []
