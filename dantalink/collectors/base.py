"""DantaLink 수집기 베이스 클래스.

모든 수집기는 이 클래스를 상속받아 일관된 인터페이스를 제공한다.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from ..models import CollectorConfig, EventSource, TriggerEvent


class BaseCollector(ABC):
    """모든 수집기의 추상 베이스.

    구현 클래스는 다음을 반드시 정의해야 한다:
      - source: EventSource 클래스 변수
      - async fetch(): TriggerEvent 리스트 반환
    """
    source: EventSource

    def __init__(self, config: CollectorConfig, name: Optional[str] = None):
        self.config = config
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"dantalink.{self.name}")

    @abstractmethod
    async def fetch(self) -> list[TriggerEvent]:
        """소스에서 데이터를 가져와 TriggerEvent 리스트로 반환.

        예외는 수집기 내부에서 처리해서 빈 리스트를 반환하는 것을 권장.
        호출자가 단일 소스 실패로 전체 파이프라인을 중단하지 않도록.
        """
        ...

    async def safe_fetch(self) -> list[TriggerEvent]:
        """fetch를 try/except로 감싼 안전 버전.

        한 소스가 실패해도 다른 소스는 계속 동작하도록 보장.
        """
        try:
            events = await self.fetch()
            self.logger.info(f"{self.name} 수집 완료: {len(events)}건")
            return events
        except Exception as e:
            self.logger.exception(f"{self.name} 수집 중 오류: {e}")
            return []
