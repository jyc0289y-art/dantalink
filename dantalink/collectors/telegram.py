"""Telegram 채널 수집기.

Telethon 기반. 진영님의 OpenClaw 작업 경험을 활용.
주의: pull 방식이 아닌 push 방식이라 다른 수집기와 패턴이 다름.
실시간 채널 모니터링을 위해서는 별도의 long-running 프로세스에서
EventCollector.run()을 호출해야 한다.

이 모듈은 timespan 동안의 과거 메시지를 가져오는 batch 모드만 구현.
실시간 모드는 향후 별도 데몬으로 분리 예정.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    from telethon import TelegramClient  # type: ignore[import-untyped]
except ImportError:
    TelegramClient = None

from ..classifier import classify, matches_any_keyword
from ..models import EventSource, TriggerEvent
from .base import BaseCollector


def _timespan_to_delta(timespan: str) -> timedelta:
    deltas = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
    }
    return deltas.get(timespan, timedelta(days=1))


class TelegramCollector(BaseCollector):
    """Telegram 채널 batch 수집기.

    필요 환경변수:
      - TG_API_ID: Telegram API ID (my.telegram.org에서 발급)
      - TG_API_HASH: Telegram API Hash
      - TG_SESSION: 세션 파일명 (기본 'dantalink')

    Args:
        channels: 모니터링할 채널 username 리스트.
    """

    source = EventSource.TELEGRAM

    def __init__(
        self,
        config,
        channels: list[str],
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        session: str = "dantalink",
        name: Optional[str] = None,
    ):
        super().__init__(config, name)
        self.channels = channels
        self.api_id = api_id or int(os.getenv("TG_API_ID", "0"))
        self.api_hash = api_hash or os.getenv("TG_API_HASH", "")
        self.session = session

    async def fetch(self) -> list[TriggerEvent]:
        if TelegramClient is None:
            self.logger.error(
                "telethon 미설치. `pip install telethon` 실행 필요"
            )
            return []
        if not self.api_id or not self.api_hash:
            self.logger.warning(
                "Telegram API 자격증명 없음. TG_API_ID / TG_API_HASH 설정 필요"
            )
            return []
        if not self.channels:
            self.logger.warning("모니터링할 채널이 없음")
            return []

        cutoff = datetime.now(timezone.utc) - _timespan_to_delta(self.config.timespan)
        events: list[TriggerEvent] = []

        client = TelegramClient(self.session, self.api_id, self.api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                self.logger.error(
                    "Telegram 인증 안 됨. CLI로 1회 로그인 필요: "
                    "python -m dantalink.cli telegram-login"
                )
                return []

            for channel in self.channels:
                try:
                    async for msg in client.iter_messages(
                        channel,
                        limit=self.config.max_records_per_source,
                    ):
                        if msg.date < cutoff:
                            break
                        event = self._build_event(msg, channel)
                        if event:
                            events.append(event)
                except Exception as e:
                    self.logger.error(f"채널 {channel} 수집 실패: {e}")
                    continue
        finally:
            await client.disconnect()

        if not self.config.keywords:
            return events

        return [
            ev for ev in events
            if matches_any_keyword(ev.title + " " + ev.body, self.config.keywords)
        ]

    def _build_event(self, msg, channel: str) -> Optional[TriggerEvent]:
        """Telethon Message를 TriggerEvent로 변환."""
        text = (msg.text or msg.message or "").strip()
        if not text:
            return None

        # 첫 줄을 제목으로, 나머지를 본문으로
        lines = text.split("\n", 1)
        title = lines[0][:200]
        body = lines[1].strip() if len(lines) > 1 else ""

        category, matched_kw = classify(text)

        # 메시지 URL은 채널 username 기반으로 생성 가능
        msg_url = f"https://t.me/{channel.lstrip('@')}/{msg.id}"

        return TriggerEvent(
            event_id=TriggerEvent.make_id(self.source, f"{channel}/{msg.id}"),
            source=self.source,
            title=title,
            body=body[:2000],
            url=msg_url,
            published_at=msg.date,
            collected_at=TriggerEvent.now_utc(),
            category=category,
            keywords=matched_kw,
            entities=[],
            raw_payload={
                "channel": channel,
                "msg_id": msg.id,
                "views": getattr(msg, "views", None),
            },
        )
