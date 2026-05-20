"""기본 사용 예시.

실행:
    cd dantalink
    python examples/basic_scan.py
"""
import asyncio
import logging

from dantalink import CollectionPipeline, CollectorConfig
from dantalink.collectors import GDELTCollector, RSSCollector


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = CollectorConfig(
        keywords=["에볼라", "WHO", "AI", "샘 알트먼"],
        timespan="24h",
        max_records_per_source=30,
    )

    # 핸들러: 수집된 이벤트를 콘솔에 예쁘게 출력
    async def print_event(event):
        print(
            f"  [{event.source.value:8s}] [{event.category.value:12s}] "
            f"keywords={event.keywords[:3]}"
        )
        print(f"    {event.title[:100]}")

    pipeline = (
        CollectionPipeline()
        .register(GDELTCollector(config))
        .register(RSSCollector(config))
        .on_event(print_event)
    )

    events = await pipeline.run_once()

    print(f"\n=== 총 {len(events)}건 수집 ===")

    # 카테고리별 분포
    by_cat = {}
    for ev in events:
        by_cat.setdefault(ev.category.value, []).append(ev)

    print("\n카테고리별 상위 3건:")
    for cat, evs in by_cat.items():
        print(f"\n[{cat.upper()}] ({len(evs)}건)")
        for ev in evs[:3]:
            print(f"  - {ev.title[:80]}")


if __name__ == "__main__":
    asyncio.run(main())
