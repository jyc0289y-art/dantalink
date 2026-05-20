"""DART(금융감독원 전자공시시스템) 공시 수집기.

신청: https://opendart.fss.or.kr/
무료, 일 10,000건 한도, API Key 필요 (환경변수 DART_API_KEY).

주요 API:
  - list.json: 공시 검색
  - document.xml: 공시 본문

NOTE: 본 모듈은 원래 `krx.py`로 명명되어 있었으나, 실제로는 KRX(한국거래소)가
아닌 DART(금감원 전자공시) API를 호출하므로 이름 충돌을 피하기 위해 `dart.py`
로 분리되었다. `krx.py`는 backward compat을 위한 deprecated alias로 유지.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from ..classifier import classify, matches_any_keyword
from ..models import EventSource, TriggerEvent
from .base import BaseCollector


DART_BASE_URL = "https://opendart.fss.or.kr/api"


def _timespan_to_dates(timespan: str) -> tuple[str, str]:
    """timespan 문자열을 (bgn_de, end_de) 형식으로 변환.

    DART는 YYYYMMDD 형식 요구.
    """
    now = datetime.now(timezone.utc)
    deltas = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
    }
    delta = deltas.get(timespan, timedelta(days=1))
    bgn = now - delta
    return bgn.strftime("%Y%m%d"), now.strftime("%Y%m%d")


class DARTCollector(BaseCollector):
    """DART OpenAPI 기반 공시 수집기.

    API Key는 다음 순서로 탐색:
      1. 생성자 인자 api_key
      2. 환경변수 DART_API_KEY
      3. None → 동작 비활성화 (경고 로그)
    """

    source = EventSource.DART

    def __init__(
        self,
        config,
        api_key: Optional[str] = None,
        name: Optional[str] = None,
    ):
        super().__init__(config, name)
        self.api_key = api_key or os.getenv("DART_API_KEY")
        if not self.api_key:
            self.logger.warning(
                "DART API key 없음. 환경변수 DART_API_KEY 설정 또는 api_key 인자 전달 필요"
            )

    async def fetch(self) -> list[TriggerEvent]:
        if not self.api_key:
            return []

        bgn_de, end_de = _timespan_to_dates(self.config.timespan)
        events: list[TriggerEvent] = []

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.get(
                    f"{DART_BASE_URL}/list.json",
                    params={
                        "crtfc_key": self.api_key,
                        "bgn_de": bgn_de,
                        "end_de": end_de,
                        "page_count": self.config.max_records_per_source,
                        "sort": "date",
                        "sort_mth": "desc",
                    },
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as e:
                self.logger.error(f"DART HTTP 오류: {e}")
                return []
            except ValueError as e:
                self.logger.error(f"DART JSON 파싱 실패: {e}")
                return []

        status = data.get("status")
        if status != "000":
            self.logger.warning(
                f"DART API status={status}, message={data.get('message')}"
            )
            return []

        for item in data.get("list", []):
            event = self._build_event(item)
            if event:
                events.append(event)

        if not self.config.keywords:
            return events

        filtered = [
            ev for ev in events
            if matches_any_keyword(
                ev.title + " " + ev.body, self.config.keywords
            )
            or matches_any_keyword(
                ev.raw_payload.get("corp_name", ""), self.config.keywords
            )
        ]
        return filtered

    def _build_event(self, item: dict) -> Optional[TriggerEvent]:
        """DART 공시 항목을 TriggerEvent로 변환."""
        corp_name = item.get("corp_name", "")
        report_nm = item.get("report_nm", "")
        rcept_no = item.get("rcept_no")
        if not corp_name or not report_nm or not rcept_no:
            return None

        title = f"[공시] {corp_name} · {report_nm}"
        url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"

        rcept_dt = item.get("rcept_dt", "")
        try:
            published_at = datetime.strptime(rcept_dt, "%Y%m%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            published_at = TriggerEvent.now_utc()

        category, matched_kw = classify(title)

        return TriggerEvent(
            event_id=TriggerEvent.make_id(self.source, rcept_no),
            source=self.source,
            title=title,
            body="",
            url=url,
            published_at=published_at,
            collected_at=TriggerEvent.now_utc(),
            category=category,
            keywords=matched_kw,
            entities=[corp_name],
            raw_payload={
                "corp_name": corp_name,
                "corp_code": item.get("corp_code"),
                "stock_code": item.get("stock_code"),
                "report_nm": report_nm,
                "rcept_no": rcept_no,
                "flr_nm": item.get("flr_nm"),
            },
        )
