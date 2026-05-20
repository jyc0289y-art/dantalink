"""DantaLink 수집 파이프라인.

여러 수집기를 병렬로 실행하고 결과를 통합한다.
이벤트 핸들러(콜백)를 등록해 실시간 처리 가능.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Optional

from .collectors import BaseCollector
from .models import TriggerEvent


# 이벤트 핸들러 타입: TriggerEvent를 받아 처리하는 async 함수
EventHandler = Callable[[TriggerEvent], Awaitable[None]]


class CollectionPipeline:
    """수집기들을 오케스트레이션하는 파이프라인.

    사용 예:
        pipeline = CollectionPipeline()
        pipeline.register(GDELTCollector(config))
        pipeline.register(RSSCollector(config))
        pipeline.on_event(my_handler)
        events = await pipeline.run_once()
    """

    def __init__(self):
        self.collectors: list[BaseCollector] = []
        self.handlers: list[EventHandler] = []
        self.logger = logging.getLogger("dantalink.pipeline")

    def register(self, collector: BaseCollector) -> "CollectionPipeline":
        """수집기 등록. 체이닝 가능."""
        self.collectors.append(collector)
        self.logger.info(f"수집기 등록: {collector.name}")
        return self

    def on_event(self, handler: EventHandler) -> "CollectionPipeline":
        """이벤트 핸들러 등록. 체이닝 가능."""
        self.handlers.append(handler)
        return self

    async def run_once(self) -> list[TriggerEvent]:
        """모든 수집기를 1회 실행하고 통합 결과 반환.

        - 각 수집기는 safe_fetch로 실행 (개별 실패가 전체를 막지 않음)
        - 등록된 핸들러는 각 이벤트마다 호출됨
        - event_id 기준 전체 중복 제거
        """
        if not self.collectors:
            self.logger.warning("등록된 수집기가 없음")
            return []

        self.logger.info(f"파이프라인 시작: {len(self.collectors)}개 수집기")
        tasks = [c.safe_fetch() for c in self.collectors]
        results = await asyncio.gather(*tasks)

        # 통합 + 중복 제거 + 시간 역순 정렬
        all_events: list[TriggerEvent] = []
        seen: set[str] = set()
        for events in results:
            for ev in events:
                if ev.event_id not in seen:
                    seen.add(ev.event_id)
                    all_events.append(ev)

        all_events.sort(key=lambda e: e.published_at, reverse=True)
        self.logger.info(f"파이프라인 완료: 총 {len(all_events)}건 (중복 제거 후)")

        # 핸들러 호출 (각 핸들러 실패가 다른 핸들러를 막지 않도록)
        for event in all_events:
            for handler in self.handlers:
                try:
                    await handler(event)
                except Exception as e:
                    self.logger.exception(f"핸들러 실패: {e}")

        return all_events

    async def run_loop(
        self,
        interval_seconds: int = 300,
        max_iterations: Optional[int] = None,
    ) -> None:
        """주기적으로 파이프라인을 실행.

        Args:
            interval_seconds: 실행 간격 (기본 5분).
            max_iterations: 최대 반복 횟수. None이면 무한 루프.
        """
        iteration = 0
        while True:
            iteration += 1
            self.logger.info(f"=== 반복 {iteration} 시작 ===")
            await self.run_once()

            if max_iterations is not None and iteration >= max_iterations:
                self.logger.info(f"최대 반복 횟수 도달: {max_iterations}")
                break

            self.logger.info(f"{interval_seconds}초 대기")
            await asyncio.sleep(interval_seconds)
