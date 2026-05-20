"""DEPRECATED: KRX → DART rename.

이 모듈은 backward compatibility만을 위해 유지된다.
실제로는 KRX(한국거래소)가 아닌 DART(금감원 전자공시) API를 호출하므로
명명상 혼동을 피하기 위해 `dantalink.collectors.dart`로 분리되었다.

새 코드에서는 `DARTCollector`를 직접 사용하라:

    from dantalink.collectors import DARTCollector

향후 진짜 KRX(한국거래소) 시세/체결 API 수집기가 추가될 때 이 모듈은 제거 예정.
"""
from __future__ import annotations

import warnings

from .dart import DARTCollector


class KRXCollector(DARTCollector):
    """[Deprecated] DARTCollector의 별칭. 인스턴스 생성 시 1회 경고."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "KRXCollector is deprecated; use DARTCollector instead. "
            "(원래 이 클래스는 KRX가 아닌 DART API를 호출하므로 이름이 변경됨)",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["KRXCollector"]
