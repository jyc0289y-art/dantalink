# DantaLink

> 행동재무 기반 한국시장 단타 발굴 시스템
> SeouLink 산하 프로젝트 · Stage 01 (데이터 수집 레이어)

음운 매칭 / 카테고리 매칭 / 약한 연결 매칭을 통해 인지 편향 기반 단기 매매 기회를 시스템적으로 포착합니다.

## 설치

```bash
cd dantalink
pip install -e .
# Telegram 수집기 사용하려면
pip install -e ".[telegram]"
```

## 빠른 시작

### CLI

```bash
# GDELT + RSS + KRX 동시 스캔
dantalink scan --keywords "에볼라,AI,샘 알트먼" --timespan 24h

# 특정 소스만
dantalink scan --keywords "에볼라" --sources gdelt,rss

# JSON으로 저장
dantalink scan --keywords "분디부교,WHO" --output events.json
```

### Python 코드

```python
import asyncio
from dantalink import CollectionPipeline, CollectorConfig
from dantalink.collectors import GDELTCollector, RSSCollector

async def main():
    config = CollectorConfig(
        keywords=["에볼라", "WHO", "AI", "샘 알트먼"],
        timespan="24h",
        max_records_per_source=30,
    )

    pipeline = (
        CollectionPipeline()
        .register(GDELTCollector(config))
        .register(RSSCollector(config))
    )

    events = await pipeline.run_once()
    for ev in events:
        print(f"[{ev.category.value}] {ev.title}")

asyncio.run(main())
```

### 환경변수

```bash
# DART (공시) 사용 시
export DART_API_KEY="your_dart_api_key"

# Telegram 사용 시 (현재는 batch CLI 미지원, 향후 별도 데몬으로 분리 예정)
export TG_API_ID="12345"
export TG_API_HASH="abcdef..."
```

> **Telegram 수집기**는 push 방식(실시간 채널 모니터링)이라 다른 수집기와 흐름이 달라, `dantalink scan` 명령에 포함되지 않습니다. 라이브러리로 직접 호출하거나 향후 별도 데몬 프로세스로 분리할 예정입니다. 자세한 내용은 `dantalink/collectors/telegram.py` 모듈 docstring 참고.

## 프로젝트 구조

```
dantalink/
├── CLAUDE.md                  # Claude Code 작업 프로토콜
├── README.md                  # 이 파일
├── dantalink/                 # 메인 패키지
│   ├── __init__.py
│   ├── cli.py                 # CLI 진입점
│   ├── pipeline.py            # 수집 오케스트레이션
│   ├── models/                # TriggerEvent 등 데이터 모델
│   ├── classifier/            # 휴리스틱 카테고리 분류기
│   └── collectors/            # 4가지 수집기
│       ├── base.py
│       ├── gdelt.py
│       ├── rss.py
│       ├── dart.py            # 금감원 전자공시 (구 krx.py)
│       ├── krx.py             # deprecated alias → dart.py
│       └── telegram.py
├── docs/                      # 설계 문서
│   ├── DantaLink_방법론.md         # 5-Stage 방법론 (학술 근거 포함)
│   ├── DantaLink_시각화.html       # 인터랙티브 시각화 (수식 포함)
│   ├── DantaLink_데이터수집기.html # Stage 01 GUI 프로토타입 (HOBIS 미학)
│   └── DantaLink_데이터수집기_문서.md
├── examples/                  # 사용 예시
└── tests/                     # 단위 테스트
```

## 테스트

```bash
pytest tests/ -v
```

## 다음 단계

- [x] **Stage 01** — 데이터 수집 레이어
- [ ] **Stage 02** — 매칭 후보 생성 (음운/카테고리/약한 연결)
- [ ] **Stage 03** — 진입 신호 검증
- [ ] **Stage 04** — 포지션 사이징 (Kelly 1/4)
- [ ] **Stage 05** — 청산 규칙

## 로드맵

1. Python 백엔드 검증 (현재)
2. iPhone 앱 (TestFlight 알파)
3. iOS / Android 동시 출시

## 라이선스

Proprietary · SL Corporation
