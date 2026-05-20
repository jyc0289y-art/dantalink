"""DantaLink 데이터 모델.

Stage 02 (매칭 후보 생성)으로 인계되는 표준 데이터 형식을 정의한다.
모든 수집기(Collector)는 이 모델로 정규화된 결과를 반환해야 한다.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EventSource(str, Enum):
    """수집 소스 분류.

    KRX는 deprecated alias for DART (실제로는 KRX 한국거래소가 아닌
    DART 금감원 전자공시 API를 호출). 향후 진짜 KRX 시세 API 추가 시 분리.
    """
    GDELT = "gdelt"
    RSS = "rss"
    DART = "dart"
    KRX = "krx"  # Deprecated alias (kept for backward compat with old JSON dumps)
    TELEGRAM = "telegram"


class EventCategory(str, Enum):
    """1차 분류 카테고리. LLM 정밀 분류 전 휴리스틱 단계."""
    GEOPOLITICAL = "geopolitical"
    HEALTH = "health"
    TECH = "tech"
    PERSON = "person"
    DISASTER = "disaster"
    REGULATORY = "regulatory"
    UNKNOWN = "unknown"


@dataclass
class TriggerEvent:
    """수집된 트리거 이벤트의 표준 표현.

    Attributes:
        event_id: 중복 제거용 해시 ID (SHA256의 앞 16자리).
        source: 어느 수집기에서 왔는지.
        title: 헤드라인.
        body: 본문 (없으면 빈 문자열).
        url: 원본 URL.
        published_at: 발행 시각 (UTC).
        collected_at: 수집 시각 (UTC).
        category: 휴리스틱 1차 카테고리.
        keywords: 매칭된 키워드 목록.
        entities: 추출된 개체명 (인물·기관·지명).
        raw_payload: 원본 데이터 보존 (디버깅·재처리용).
    """
    event_id: str
    source: EventSource
    title: str
    body: str
    url: Optional[str]
    published_at: datetime
    collected_at: datetime
    category: EventCategory = EventCategory.UNKNOWN
    keywords: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화용 변환."""
        d = asdict(self)
        d["source"] = self.source.value
        d["category"] = self.category.value
        d["published_at"] = self.published_at.isoformat()
        d["collected_at"] = self.collected_at.isoformat()
        return d

    @staticmethod
    def make_id(source: EventSource, unique_key: str) -> str:
        """소스와 유니크 키 조합으로 결정론적 해시 생성.

        같은 URL/제목이 다른 소스에서 와도 다른 ID를 갖도록 source를 prefix로 사용.
        """
        raw = f"{source.value}::{unique_key}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    @staticmethod
    def now_utc() -> datetime:
        """수집 시각 표준 (UTC aware)."""
        return datetime.now(timezone.utc)


@dataclass
class CollectorConfig:
    """수집기 설정.

    각 수집기 인스턴스는 이 설정을 받아 동작한다.
    """
    keywords: list[str] = field(default_factory=list)
    timespan: str = "24h"               # 1h, 6h, 24h, 7d
    max_records_per_source: int = 50
    timeout_seconds: float = 20.0
