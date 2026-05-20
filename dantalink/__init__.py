"""DantaLink · 행동재무 기반 한국시장 단타 발굴 시스템.

SeouLink 산하 프로젝트. Stage 01 (데이터 수집 레이어).
"""
from .models import (
    CollectorConfig,
    EventCategory,
    EventSource,
    TriggerEvent,
)
from .pipeline import CollectionPipeline

__version__ = "0.1.0"
__all__ = [
    "CollectionPipeline",
    "CollectorConfig",
    "EventCategory",
    "EventSource",
    "TriggerEvent",
]
