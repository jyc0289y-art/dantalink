"""RSS 피드 수집기.

국내·외신 RSS를 비동기로 가져와 워치 키워드 매칭된 기사만 이벤트화.
feedparser는 동기 라이브러리이므로 ThreadPoolExecutor에서 실행.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

try:
    import feedparser  # type: ignore[import-untyped]
except ImportError:
    feedparser = None  # 런타임에 명확한 에러 메시지로 안내

from ..classifier import classify, matches_any_keyword
from ..models import EventSource, TriggerEvent
from .base import BaseCollector


# 기본 피드 목록. 사용자가 config로 오버라이드 가능.
# 2026-05-20 healthcheck 결과 (Phase B QC#2 이후 라이브 검증):
#   - 연합뉴스 경제: 120 entries (정상)
#   - 연합뉴스 정치: 120 entries (정상)
#   - 매일경제 증권: 50 entries (정상) — 단타 핵심 피드, 신규 추가
#   - 전자신문 IT: 30 entries (정상, ascii→utf-8 경고만)
#   - ZDNet Korea: 30 entries (정상) — IT 전문, 신규 추가
#   - 파이낸셜뉴스 경제: 34 entries (정상) — 신규 추가
#   - Bloomberg Markets: 30 entries (정상)
#   - WHO News English: 25 entries (정상)
#   ❌ Reuters businessNews: DNS 실패 (feeds.reuters.com 도메인 소멸) → GDELT가 흡수
#   ❌ 한국경제: 301/403 + entity error → URL 봉쇄, 제거
DEFAULT_FEEDS = [
    # 한국어 - 경제/IT/단타 중심
    "https://www.yna.co.kr/rss/economy.xml",                     # 연합뉴스 경제
    "https://www.yna.co.kr/rss/politics.xml",                    # 연합뉴스 정치
    "https://www.mk.co.kr/rss/50200011/",                        # 매일경제 증권 (단타 핵심)
    "https://rss.etnews.com/Section901.xml",                     # 전자신문 IT
    "https://feeds.feedburner.com/zdkorea",                      # ZDNet Korea (IT)
    "https://www.fnnews.com/rss/r20/fn_realnews_economy.xml",    # 파이낸셜뉴스 경제

    # 영어 - 글로벌 비즈니스
    "https://feeds.bloomberg.com/markets/news.rss",              # Bloomberg Markets

    # 보건 (분디부교·에볼라 같은 PHEIC 이슈)
    "https://www.who.int/rss-feeds/news-english.xml",            # WHO News English
]


def _parse_published(entry: dict) -> datetime:
    """RSS entry에서 published 시각 추출."""
    # feedparser가 published_parsed (time.struct_time)를 제공할 수 있음
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    return TriggerEvent.now_utc()


class RSSCollector(BaseCollector):
    """RSS 피드 기반 수집기.

    초기화 시 feeds 인자로 피드 URL 리스트를 받는다.
    None이면 DEFAULT_FEEDS 사용.
    """

    source = EventSource.RSS

    def __init__(
        self,
        config,
        feeds: Optional[list[str]] = None,
        name: Optional[str] = None,
    ):
        super().__init__(config, name)
        self.feeds = feeds if feeds is not None else DEFAULT_FEEDS

    async def fetch(self) -> list[TriggerEvent]:
        if feedparser is None:
            self.logger.error(
                "feedparser 미설치. `pip install feedparser` 실행 필요"
            )
            return []

        # 피드 파싱은 동기 작업이므로 to_thread로 병렬 실행
        tasks = [asyncio.to_thread(self._parse_feed, url) for url in self.feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        events: list[TriggerEvent] = []
        for url, result in zip(self.feeds, results):
            if isinstance(result, Exception):
                self.logger.error(f"피드 파싱 실패 ({url}): {result}")
                continue
            assert isinstance(result, list)
            events.extend(result)

        # event_id 기준 중복 제거
        seen: set[str] = set()
        deduped: list[TriggerEvent] = []
        for ev in events:
            if ev.event_id not in seen:
                seen.add(ev.event_id)
                deduped.append(ev)

        # 워치 키워드 매칭된 것만 반환 (키워드가 비었으면 전체)
        if not self.config.keywords:
            return deduped[: self.config.max_records_per_source]

        filtered = [
            ev for ev in deduped
            if matches_any_keyword(
                ev.title + " " + ev.body, self.config.keywords
            )
        ]
        return filtered[: self.config.max_records_per_source]

    def _parse_feed(self, feed_url: str) -> list[TriggerEvent]:
        """단일 피드 동기 파싱. asyncio.to_thread로 호출됨."""
        parsed = feedparser.parse(feed_url)
        if parsed.bozo and not parsed.entries:
            self.logger.warning(f"피드가 비어있음 ({feed_url})")
            return []

        events: list[TriggerEvent] = []
        for entry in parsed.entries[: self.config.max_records_per_source]:
            event = self._build_event(entry, feed_url)
            if event:
                events.append(event)
        return events

    def _build_event(self, entry: dict, feed_url: str) -> Optional[TriggerEvent]:
        """RSS entry를 TriggerEvent로 변환."""
        title = (entry.get("title") or "").strip()
        link = entry.get("link") or ""
        if not title or not link:
            return None

        # 본문 필드명은 피드마다 다름: summary, description, content
        body = (
            entry.get("summary")
            or entry.get("description")
            or ""
        )
        if isinstance(body, list) and body:
            body = body[0].get("value", "") if isinstance(body[0], dict) else str(body[0])
        body = str(body).strip()

        published_at = _parse_published(entry)
        category, matched_kw = classify(title + " " + body)
        watch_hits = matches_any_keyword(title + " " + body, self.config.keywords)
        all_keywords = list({*matched_kw, *watch_hits})

        return TriggerEvent(
            event_id=TriggerEvent.make_id(self.source, link),
            source=self.source,
            title=title,
            body=body[:2000],   # 본문 길이 제한
            url=link,
            published_at=published_at,
            collected_at=TriggerEvent.now_utc(),
            category=category,
            keywords=all_keywords,
            entities=[],
            raw_payload={"feed_url": feed_url},
        )
