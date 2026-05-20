"""GDELT 2.0 DOC API 수집기.

GDELT는 전 세계 뉴스를 실시간으로 모니터링하는 무료 데이터 프로젝트.
API 문서: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

주요 쿼리 옵션:
  - query: 검색 키워드 (Boolean 연산자 AND/OR 지원)
  - mode: ArtList (기사 리스트)
  - format: json
  - maxrecords: 최대 250
  - timespan: 24h, 7d 등
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

import httpx

from ..classifier import classify, matches_any_keyword
from ..models import EventCategory, EventSource, TriggerEvent
from .base import BaseCollector


GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# GDELT 서버 공식 안내: "Please limit requests to one every 5 seconds"
# (429 응답의 body로 직접 명시됨). 5초 미만으로 호출 시 IP 임시 차단.
# 5.5초 → 안전 마진 포함 (분당 ~10회 = GDELT 권장 한도).
GDELT_INTER_QUERY_SLEEP_SECONDS = 5.5


def _parse_gdelt_datetime(date_str: str) -> datetime:
    """GDELT 날짜 포맷 파싱.

    GDELT는 'seendate' 필드를 'YYYYMMDDTHHMMSSZ' 형식으로 반환.
    """
    if not date_str:
        return TriggerEvent.now_utc()
    try:
        # 20260520T013000Z 형식
        return datetime.strptime(date_str, "%Y%m%dT%H%M%SZ").replace(
            tzinfo=TriggerEvent.now_utc().tzinfo
        )
    except (ValueError, TypeError):
        return TriggerEvent.now_utc()


class GDELTCollector(BaseCollector):
    """GDELT DOC API를 통해 글로벌 뉴스를 수집한다."""

    source = EventSource.GDELT

    async def fetch(self) -> list[TriggerEvent]:
        if not self.config.keywords:
            self.logger.warning("키워드가 없어 GDELT 수집을 건너뜀")
            return []

        # GDELT는 영어 검색이 강하므로 영문 키워드 위주로 OR 조합
        # 한글 키워드도 그대로 전달은 가능하나 매칭률이 낮음
        events: list[TriggerEvent] = []

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            for i, query in enumerate(self.config.keywords):
                if i > 0:
                    # GDELT rate limit 회피용 호출 간 대기
                    await asyncio.sleep(GDELT_INTER_QUERY_SLEEP_SECONDS)
                self.logger.debug(f"GDELT query: {query}")
                try:
                    response = await client.get(
                        GDELT_BASE_URL,
                        params={
                            "query": query,
                            "mode": "ArtList",
                            "format": "json",
                            "maxrecords": self.config.max_records_per_source,
                            "timespan": self.config.timespan,
                            "sort": "DateDesc",
                        },
                        headers={
                            # User-Agent 명시 — GDELT가 익명 클라이언트를 더 빠르게 차단함
                            "User-Agent": "DantaLink/0.1 (+research)",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPError as e:
                    self.logger.error(f"GDELT HTTP 오류 (query={query}): {e}")
                    continue
                except ValueError as e:
                    self.logger.error(f"GDELT JSON 파싱 실패 (query={query}): {e}")
                    continue

                for article in data.get("articles", []):
                    event = self._build_event(article, query)
                    if event:
                        events.append(event)

        # event_id 기준 중복 제거 (여러 쿼리에서 같은 기사 잡힐 수 있음)
        seen_ids: set[str] = set()
        deduped: list[TriggerEvent] = []
        for ev in events:
            if ev.event_id not in seen_ids:
                seen_ids.add(ev.event_id)
                deduped.append(ev)

        return deduped

    def _build_event(self, article: dict, query: str) -> Optional[TriggerEvent]:
        """GDELT 기사 JSON을 TriggerEvent로 변환."""
        title = (article.get("title") or "").strip()
        url = article.get("url") or ""
        if not title or not url:
            return None

        body = ""  # GDELT ArtList는 본문 미제공. 필요하면 url 별도 fetch.
        published_at = _parse_gdelt_datetime(article.get("seendate", ""))

        # 카테고리 분류 (제목 + 가능한 본문 결합)
        category, matched_kw = classify(title + " " + body)
        watch_hits = matches_any_keyword(title, self.config.keywords)

        # 매칭 키워드는 휴리스틱 매칭 + 워치 키워드 합집합
        all_keywords = list({*matched_kw, *watch_hits, query})

        return TriggerEvent(
            event_id=TriggerEvent.make_id(self.source, url),
            source=self.source,
            title=title,
            body=body,
            url=url,
            published_at=published_at,
            collected_at=TriggerEvent.now_utc(),
            category=category,
            keywords=all_keywords,
            entities=[],   # NER은 LLM 단계에서 처리
            raw_payload={
                "domain": article.get("domain"),
                "language": article.get("language"),
                "sourcecountry": article.get("sourcecountry"),
                "query": query,
            },
        )
