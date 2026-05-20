"""DantaLink CLI.

사용 예:
    python -m dantalink.cli scan --keywords "에볼라,AI" --timespan 24h
    python -m dantalink.cli scan --keywords "에볼라" --output events.json
    python -m dantalink.cli match --input events.json --output matches.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from . import CollectionPipeline, CollectorConfig
from .collectors import DARTCollector, GDELTCollector, RSSCollector
from .models import EventCategory, EventSource, TriggerEvent


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


async def cmd_scan(args: argparse.Namespace) -> int:
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    config = CollectorConfig(
        keywords=keywords,
        timespan=args.timespan,
        max_records_per_source=args.max_records,
    )

    pipeline = CollectionPipeline()
    sources = set(args.sources.split(","))

    if "gdelt" in sources:
        pipeline.register(GDELTCollector(config))
    if "rss" in sources:
        pipeline.register(RSSCollector(config))
    if "dart" in sources or "krx" in sources:
        # 'krx'는 backward compat용 별칭. DARTCollector 직접 사용 권장.
        pipeline.register(DARTCollector(config))

    # 콘솔 출력 핸들러
    async def print_event(event):
        print(
            f"  [{event.source.value:8s}] [{event.category.value:12s}] "
            f"{event.title[:80]}"
        )

    pipeline.on_event(print_event)

    print(f"\n▶ DantaLink 스캔 시작")
    print(f"  키워드: {keywords}")
    print(f"  타임스팬: {args.timespan}")
    print(f"  소스: {sources}\n")

    events = await pipeline.run_once()

    print(f"\n✓ 수집 완료: {len(events)}건\n")

    # 카테고리별 통계
    cat_count: dict[str, int] = {}
    for ev in events:
        cat_count[ev.category.value] = cat_count.get(ev.category.value, 0) + 1
    print("카테고리별 분포:")
    for cat, n in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat:15s} {n:3d}")

    if args.output:
        out_path = Path(args.output)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(
                [ev.to_dict() for ev in events],
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"\n💾 저장 완료: {out_path}")

    return 0


def _load_events_json(path: Path) -> list[TriggerEvent]:
    """JSON 파일에서 TriggerEvent 리스트 복원."""
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    events: list[TriggerEvent] = []
    for d in raw:
        try:
            events.append(TriggerEvent(
                event_id=d["event_id"],
                source=EventSource(d["source"]),
                title=d["title"],
                body=d.get("body", ""),
                url=d.get("url"),
                published_at=datetime.fromisoformat(d["published_at"]),
                collected_at=datetime.fromisoformat(d["collected_at"]),
                category=EventCategory(d.get("category", "unknown")),
                keywords=d.get("keywords", []),
                entities=d.get("entities", []),
                raw_payload=d.get("raw_payload", {}),
            ))
        except Exception as e:
            logging.warning(f"이벤트 파싱 실패 (skip): {e}")
    return events


async def cmd_match(args: argparse.Namespace) -> int:
    """Stage 02 — 수집된 TriggerEvent를 KRX 종목 후보로 매칭."""
    # matchers는 import 비용이 있으므로 함수 내부에서 lazy import
    from .matchers import (
        KRXStockDB,
        PhonologicalMatcher,
        SemanticMatcher,
    )

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"❌ 입력 파일 없음: {in_path}")
        return 1

    print(f"\n▶ DantaLink 매칭 시작")
    print(f"  입력: {in_path}")
    events = _load_events_json(in_path)
    print(f"  이벤트: {len(events)}건\n")

    # KRX 종목 DB 로드
    db = KRXStockDB.load_default()
    print(f"  KRX 종목 DB: {len(db.stocks)}건")

    phon = PhonologicalMatcher(
        db,
        min_marcap_eok=args.min_marcap,
        max_marcap_eok=args.max_marcap,
        max_per_token=args.max_per_token,
    )
    sem = SemanticMatcher(
        db,
        min_marcap_eok=args.min_marcap,
        max_marcap_eok=args.max_marcap,
        max_per_keyword=args.max_per_keyword,
    )
    print(f"  매칭 레이어: Layer A (음운), Layer B (의미)\n")

    # 매칭 실행
    all_candidates = []           # 전체 후보 리스트
    per_stock = defaultdict(lambda: {
        "stock_code": "",
        "stock_name": "",
        "market": "",
        "marcap_eok": 0,
        "total_score": 0.0,
        "max_score": 0.0,
        "match_count": 0,
        "layers": set(),
        "matches": [],
    })

    for ev in events:
        cands = phon.safe_match(ev) + sem.safe_match(ev)
        for c in cands:
            all_candidates.append({
                "trigger_event_id": c.trigger_event_id,
                "event_title": ev.title,
                "event_category": ev.category.value,
                "event_url": ev.url,
                "stock_code": c.stock_code,
                "stock_name": c.stock_name,
                "market": c.market,
                "marcap_eok": c.marcap_eok,
                "layer": c.layer,
                "score": round(c.score, 3),
                "matched_on": c.matched_on,
                "reason": c.reason,
            })
            agg = per_stock[c.stock_code]
            agg["stock_code"] = c.stock_code
            agg["stock_name"] = c.stock_name
            agg["market"] = c.market
            agg["marcap_eok"] = c.marcap_eok
            agg["total_score"] += c.score
            if c.score > agg["max_score"]:
                agg["max_score"] = c.score
            agg["match_count"] += 1
            agg["layers"].add(c.layer)
            agg["matches"].append({
                "event_title": ev.title,
                "event_category": ev.category.value,
                "layer": c.layer,
                "score": round(c.score, 3),
                "matched_on": c.matched_on,
            })

    # 종목별 종합 — max_score 우선, total_score 보조 (단일 강한 신호가 다중 약한 신호보다 우선)
    sort_key = (
        (lambda x: (x["max_score"], x["total_score"]))
        if args.sort == "max"
        else (lambda x: (x["total_score"], x["max_score"]))
    )
    top_stocks = sorted(per_stock.values(), key=sort_key, reverse=True)[: args.top]

    print(f"✓ 매칭 완료: 전체 후보 {len(all_candidates)}건, 고유 종목 {len(per_stock)}개")
    print(f"  정렬 기준: {args.sort} ({'최고 단일 매칭' if args.sort == 'max' else '총점'})\n")
    print(f"=== 상위 {args.top} 종목 후보 ===")
    print(
        f"{'순위':>4} {'코드':>7} {'종목명':<22} {'시장':<14} "
        f"{'시총(억)':>10} {'Max':>5} {'Total':>6} {'매칭':>4} {'레이어':<22}"
    )
    print("-" * 115)
    for i, s in enumerate(top_stocks, start=1):
        layers_str = ",".join(sorted(s["layers"]))
        print(
            f"{i:>4} {s['stock_code']:>7} {s['stock_name'][:21]:<22} "
            f"{s['market']:<14} {s['marcap_eok']:>10,} "
            f"{s['max_score']:>5.2f} {s['total_score']:>6.2f} {s['match_count']:>4} {layers_str:<22}"
        )

    # JSON 저장
    if args.output:
        out_path = Path(args.output)
        # set → list 변환 (JSON 직렬화)
        for s in per_stock.values():
            s["layers"] = sorted(s["layers"])
        with out_path.open("w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "input_events": str(in_path),
                "event_count": len(events),
                "stock_db_count": len(db.stocks),
                "filter": {
                    "min_marcap_eok": args.min_marcap,
                    "max_per_token": args.max_per_token,
                    "max_per_keyword": args.max_per_keyword,
                },
                "top_stocks": top_stocks,
                "all_candidates": all_candidates,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n💾 저장 완료: {out_path}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dantalink",
        description="DantaLink · Data Collection CLI",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="DEBUG 로그")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="1회 수집 실행")
    scan.add_argument(
        "--keywords",
        required=True,
        help="콤마로 구분된 키워드. 예: 에볼라,AI,샘 알트먼",
    )
    scan.add_argument(
        "--timespan",
        default="24h",
        choices=["1h", "6h", "24h", "7d"],
        help="조회 기간 (기본 24h)",
    )
    scan.add_argument(
        "--sources",
        default="gdelt,rss,dart",
        help="콤마로 구분된 소스 (기본: gdelt,rss,dart). 'krx'는 'dart' 별칭(deprecated).",
    )
    scan.add_argument(
        "--max-records",
        type=int,
        default=50,
        help="소스당 최대 레코드 수 (기본 50)",
    )
    scan.add_argument(
        "--output",
        help="결과를 JSON으로 저장할 경로",
    )
    scan.set_defaults(func=cmd_scan)

    # match 서브명령 (Stage 02)
    match = sub.add_parser("match", help="수집된 이벤트를 KRX 종목 후보로 매칭")
    match.add_argument(
        "--input",
        required=True,
        help="scan 결과 JSON 파일 (예: events.json)",
    )
    match.add_argument(
        "--output",
        help="매칭 결과 JSON 저장 경로 (예: matches.json)",
    )
    match.add_argument(
        "--top",
        type=int,
        default=20,
        help="상위 N개 종목 후보 출력 (기본 20)",
    )
    match.add_argument(
        "--min-marcap",
        type=int,
        default=500,
        dest="min_marcap",
        help="후보 종목 최소 시가총액(억원). 기본 500. 소형주는 0으로 설정",
    )
    match.add_argument(
        "--max-marcap",
        type=int,
        default=None,
        dest="max_marcap",
        help="후보 종목 최대 시가총액(억원). 단타는 5000 이하 권장 (방법론.md §4 Stage 3)",
    )
    match.add_argument(
        "--max-per-token",
        type=int,
        default=3,
        dest="max_per_token",
        help="Layer A(음운) 단일 토큰당 최대 후보 (기본 3)",
    )
    match.add_argument(
        "--max-per-keyword",
        type=int,
        default=5,
        dest="max_per_keyword",
        help="Layer B(의미) 단일 키워드당 최대 후보 (기본 5)",
    )
    match.add_argument(
        "--sort",
        choices=["max", "total"],
        default="max",
        help="정렬 기준: max=단일 매칭 최고 점수 우선 (기본), total=총점 우선",
    )
    match.set_defaults(func=cmd_match)

    return parser


def main() -> int:
    # 윈도우 콘솔(cp949)에서도 ✓/▶/💾 같은 유니코드 출력이 깨지지 않도록 UTF-8 강제
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
