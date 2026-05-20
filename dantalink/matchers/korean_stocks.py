"""KRX 상장 종목 DB — 음절 인덱스 기반 빠른 매칭.

데이터 출처: FinanceDataReader (`fdr.StockListing('KRX')`).
CSV 캐시: `data/krx_stocks.csv` (UTF-8 with BOM).

음절 인덱스 구조:
  - by_first_syllable["샘"] → [샘표, 샘아일랜드, ...]
  - by_substring[(2글자 substring)] → 종목 리스트 (Layer C용)
"""
from __future__ import annotations

import csv
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_logger = logging.getLogger("dantalink.matchers.korean_stocks")


@dataclass
class KRXStock:
    """한 종목의 마스터 데이터."""
    code: str
    name: str
    market: str
    marcap_eok: int = 0
    stocks: int = 0
    # 파생 필드 (post_init)
    syllables: list[str] = field(default_factory=list)

    def __post_init__(self):
        # 종목명을 음절 단위로 분리 (한글 1글자 = 1음절, 영문/숫자도 포함)
        self.syllables = list(self.name)


class KRXStockDB:
    """KRX 종목 마스터 DB + 인덱스.

    사용 예:
        db = KRXStockDB.load_default()
        for stock in db.find_by_first_syllable("샘"):
            print(stock.code, stock.name)
    """

    def __init__(self, stocks: list[KRXStock]):
        self.stocks: list[KRXStock] = stocks
        self.by_code: dict[str, KRXStock] = {s.code: s for s in stocks}
        # 음절 인덱스: 첫 음절 → 종목 리스트
        self.by_first_syllable: dict[str, list[KRXStock]] = defaultdict(list)
        # 2-gram 인덱스 (Layer B substring 매칭용)
        self.by_substring: dict[str, list[KRXStock]] = defaultdict(list)
        for s in stocks:
            if s.syllables:
                self.by_first_syllable[s.syllables[0]].append(s)
            # 2자 substring 인덱스 (예: "백신" → [차백신연구소, ...])
            for i in range(len(s.name) - 1):
                bigram = s.name[i:i + 2]
                if bigram not in self.by_substring or s not in self.by_substring[bigram]:
                    self.by_substring[bigram].append(s)
        _logger.info(
            f"KRXStockDB 로드 완료: {len(stocks)}건 종목, "
            f"{len(self.by_first_syllable)}개 시작음절, "
            f"{len(self.by_substring)}개 bigram"
        )

    @classmethod
    def load_csv(cls, csv_path: Path) -> "KRXStockDB":
        """CSV 파일에서 로드 (FinanceDataReader 슬림 포맷)."""
        stocks: list[KRXStock] = []
        # utf-8-sig: BOM 자동 처리
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = (row.get("Code") or "").strip()
                name = (row.get("Name") or "").strip()
                if not code or not name:
                    continue
                marcap_raw = row.get("Marcap_억원") or "0"
                try:
                    marcap_eok = int(float(marcap_raw)) if marcap_raw and marcap_raw != "<NA>" else 0
                except ValueError:
                    marcap_eok = 0
                stocks_raw = row.get("Stocks") or "0"
                try:
                    stocks_count = int(stocks_raw) if stocks_raw and stocks_raw != "<NA>" else 0
                except ValueError:
                    stocks_count = 0
                stocks.append(KRXStock(
                    code=code,
                    name=name,
                    market=(row.get("Market") or "").strip(),
                    marcap_eok=marcap_eok,
                    stocks=stocks_count,
                ))
        return cls(stocks)

    @classmethod
    def load_default(cls) -> "KRXStockDB":
        """기본 위치(`<project_root>/data/krx_stocks.csv`)에서 로드.

        프로젝트 루트는 `dantalink/` 패키지에서 2단계 상위.
        """
        pkg_dir = Path(__file__).resolve().parent.parent  # .../DantaLink/dantalink
        proj_root = pkg_dir.parent                          # .../DantaLink
        csv_path = proj_root / "data" / "krx_stocks.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"KRX 종목 DB CSV가 없음: {csv_path}\n"
                f"먼저 다음 스크립트 실행:\n"
                f"  python -c \"import FinanceDataReader as fdr; "
                f"df = fdr.StockListing('KRX'); df.to_csv('{csv_path}', index=False)\""
            )
        return cls.load_csv(csv_path)

    def find_by_first_syllable(self, syllable: str) -> list[KRXStock]:
        """첫 음절 정확 일치 (Layer A 음운 매칭)."""
        return list(self.by_first_syllable.get(syllable, []))

    def find_by_substring(self, substring: str) -> list[KRXStock]:
        """종목명에 substring이 포함된 종목 (Layer B/C).

        2자 이상이면 bigram 인덱스로 후보 줄이고 최종 in 체크.
        1자이면 전체 스캔.
        """
        if len(substring) < 1:
            return []
        if len(substring) == 1:
            # 단일 음절 검색 — 첫 음절 + 후속 위치 둘 다
            results = []
            for s in self.stocks:
                if substring in s.name:
                    results.append(s)
            return results
        # 2자+: bigram 후보 → 정확 매칭
        candidates = self.by_substring.get(substring[:2], [])
        if len(substring) == 2:
            return list(candidates)
        # 3자+: candidates 중 substring 정확 포함
        return [s for s in candidates if substring in s.name]
