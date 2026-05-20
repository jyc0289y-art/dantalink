"""데이터 모델 단위 테스트."""
from datetime import datetime, timezone

from dantalink.models import (
    CollectorConfig,
    EventCategory,
    EventSource,
    TriggerEvent,
)


def test_make_id_deterministic():
    id1 = TriggerEvent.make_id(EventSource.GDELT, "https://example.com/a")
    id2 = TriggerEvent.make_id(EventSource.GDELT, "https://example.com/a")
    assert id1 == id2
    assert len(id1) == 16


def test_make_id_source_separated():
    """같은 키여도 source가 다르면 ID 다름."""
    id1 = TriggerEvent.make_id(EventSource.GDELT, "abc")
    id2 = TriggerEvent.make_id(EventSource.RSS, "abc")
    assert id1 != id2


def test_now_utc_has_tz():
    now = TriggerEvent.now_utc()
    assert now.tzinfo is not None


def test_to_dict_serialization():
    ev = TriggerEvent(
        event_id="abc123",
        source=EventSource.GDELT,
        title="Test event",
        body="Body text",
        url="https://example.com",
        published_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        collected_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        category=EventCategory.HEALTH,
        keywords=["WHO", "에볼라"],
    )
    d = ev.to_dict()
    assert d["source"] == "gdelt"
    assert d["category"] == "health"
    assert d["published_at"].startswith("2026-05-20")
    assert d["keywords"] == ["WHO", "에볼라"]


def test_config_defaults():
    c = CollectorConfig()
    assert c.timespan == "24h"
    assert c.max_records_per_source == 50
    assert c.keywords == []
