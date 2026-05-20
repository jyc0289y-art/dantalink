"""DantaLink 수집기 패키지."""
from .base import BaseCollector
from .dart import DARTCollector
from .gdelt import GDELTCollector
from .krx import KRXCollector  # Deprecated alias for DARTCollector
from .rss import RSSCollector
from .telegram import TelegramCollector

__all__ = [
    "BaseCollector",
    "DARTCollector",
    "GDELTCollector",
    "KRXCollector",  # Deprecated
    "RSSCollector",
    "TelegramCollector",
]
