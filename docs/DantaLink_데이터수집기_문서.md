# DantaLink · Data Collection Layer

> Stage 01: 트리거 이벤트 감지 모듈
> 디자인 시스템: HOBIS (Terran Console Aesthetic)
> 작성일: 2026.05.20

---

## 📋 개요

DantaLink 방법론의 **Stage 01 (트리거 이벤트 감지)** 을 담당하는 GUI 콘솔이다. SeouLink 인프라의 HOBIS 디자인 언어를 계승하여, 진영님이 익숙한 운용 미학(스타크래프트 테란 컨솔)을 유지한다.

현재 구현은 **Frontend Mock**이며, 키워드/소스 토글/타임스팬 등 운영 인터페이스와 시뮬레이션 로직이 완성된 상태다. 다음 단계로 실제 백엔드 어댑터를 연결하면 즉시 작동한다.

---

## 🎨 디자인 시스템 (Terran Console)

### 컬러 토큰

| 토큰 | 값 | 용도 |
|------|-----|------|
| `--bg-void` | `#050810` | 최하층 배경 (콘솔) |
| `--bg-deep` | `#0a0f17` | 메인 배경 |
| `--bg-panel` | `#131820` | 패널 배경 |
| `--bg-elevated` | `#1a212c` | 호버/액티브 배경 |
| `--bg-input` | `#0e131b` | 입력 필드 배경 |
| `--border` | `#2a3441` | 표준 보더 |
| `--ink` | `#c8d4e0` | 본문 텍스트 |
| `--terran` | `#ffb627` | 테란 시그니처 옐로우 |
| `--cyan` | `#4ecdc4` | HUD 액센트 |
| `--red` | `#ff3a3a` | 경고/긴급 |
| `--green` | `#4ade80` | 정상 작동 |
| `--orange` | `#ff8c42` | 주의 |

### 타이포그래피

- **본문/콘솔**: `JetBrains Mono` 12-13px
- **디스플레이 (헤더·버튼)**: `Orbitron` 13-16px, letter-spacing 0.25em
- **라벨**: uppercase + letter-spacing 0.2em (테란 HMI 표준)

### 인터랙션 효과

- **스캔라인 오버레이**: 반복 그라데이션으로 CRT 느낌 (3px 주기, 1.5% 투명도)
- **CRT 비넷팅**: radial gradient로 화면 가장자리 어둡게
- **글로우**: 테란 옐로우 액티브 상태에 box-shadow로 발광
- **펄스 LED**: 정상 작동 인디케이터 (2초 주기)
- **다이아몬드 클립**: 메인 실행 버튼 (`clip-path: polygon`)

### 레이아웃 구조

```
┌─────────────────────────────────────────────────────┐
│ HEADER · 로고 / 시스템 상태 / UTC 시계                │
├──────────┬──────────────────────────┬───────────────┤
│          │                          │               │
│ CONTROL  │     SYSTEM CONSOLE       │  COLLECTED    │
│  PANEL   │  (스크롤링 로그 출력)    │   EVENTS      │
│          │                          │               │
│ 320px    │      1fr (가변)          │   380px       │
├──────────┴──────────────────────────┴───────────────┤
│ FOOTER · 시스템 메시지 / 보안 채널 표시              │
└─────────────────────────────────────────────────────┘
```

---

## 🎮 사용법

### 1. 데이터 소스 토글
좌측 패널 상단의 4개 소스 (GDELT, RSS, KRX/DART, Telegram) 클릭하여 활성/비활성 전환. 활성 상태에서 좌측에 테란 옐로우 인디케이터 발광.

### 2. 키워드 관리
입력 필드에 키워드 입력 후 Enter 또는 `+ ADD` 버튼. 기본값:
- `에볼라`, `WHO`, `AI`, `샘 알트먼`

키워드 칩의 `✕` 클릭으로 제거.

### 3. 타임스팬 선택
1H / 6H / 24H / 7D 중 선택. 기본값 24H.

### 4. 스캔 실행
하단의 `▶ INITIATE SCAN` 버튼 클릭:
1. 활성화된 소스 순차 호출
2. 콘솔에 실시간 로그 출력
3. 우측 패널에 이벤트 카드 카테고리별 색상으로 표시
4. 통계 자동 업데이트

스캔 중 버튼이 `■ ABORT SCAN`으로 변경되며 클릭 시 즉시 중단.

---

## 📊 이벤트 카테고리 (휴리스틱 분류)

LLM 분류 전 단계에서 키워드 사전 기반으로 1차 분류를 수행한다.

| 카테고리 | 색상 | 키워드 예시 |
|---------|------|------------|
| `HEALTH` | 🔴 Red | WHO, CDC, PHEIC, 에볼라, 바이러스, 백신, 분디부교 |
| `GEOPOLITICAL` | 🟠 Orange | 전쟁, 미사일, 제재, 정상회담, 이란, 관세 |
| `TECH` | 🔵 Cyan | OpenAI, GPT, Claude, AI, 반도체, HBM, NVIDIA |
| `PERSON` | 🟡 Terran | 방한, 내한, 회담, CEO, 대통령, visit, speech |
| `DISASTER` | 🔴 Red | 지진, 쓰나미, 화재, 폭발, 사고 |
| `REGULATORY` | 🟣 Violet | 금리, FOMC, 한은, 규제, 법안 |

분류 알고리즘은 가장 많은 키워드가 매칭된 카테고리를 채택한다 (Stage 02에서 LLM 분류기가 정밀화).

---

## 🔌 백엔드 연결 가이드 (다음 단계)

현재는 Mock 데이터로 시뮬레이션 작동한다. 실제 운영을 위해 다음 어댑터를 구현해야 한다.

### Architecture

```
[ Frontend GUI (현재 완성) ]
            ↓
    WebSocket / SSE
            ↓
[ Backend Server (Python FastAPI) ]
            ├─ GDELTCollector
            ├─ RSSCollector
            ├─ KRXCollector
            └─ TelegramCollector
            ↓
[ Heuristic Classifier ]
            ↓
[ TriggerEvent Stream → Stage 02 ]
```

### GDELT Adapter

GDELT 2.0 DOC API는 무료, 인증 불필요.

```python
import httpx

GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

async def fetch_gdelt(query: str, timespan: str = "24h", max_records: int = 50):
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "timespan": timespan,
        "sort": "DateDesc",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(GDELT_BASE, params=params)
        r.raise_for_status()
        return r.json().get("articles", [])
```

**참고**: GDELT 쿼리는 부울 연산자 지원 (`AND`, `OR`, `NOT`, `near`). 한국어 직접 검색은 약하니 영어 키워드 위주로 구성.

### RSS Adapter

`feedparser` 라이브러리 사용.

```python
import feedparser
import asyncio

FEEDS = [
    "https://www.reutersagency.com/feed/?best-topics=business-finance",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://rss.etnews.com/Section901.xml",  # 전자신문 IT
    "https://www.yna.co.kr/rss/economy.xml",  # 연합 경제
]

async def fetch_rss(url: str):
    loop = asyncio.get_event_loop()
    feed = await loop.run_in_executor(None, feedparser.parse, url)
    return feed.entries
```

### KRX/DART Adapter

DART (Data Analysis, Retrieval and Transfer System) Open API 사용.
- 신청: https://opendart.fss.or.kr
- 무료, 일 10,000건 한도
- API Key 필요

```python
DART_BASE = "https://opendart.fss.or.kr/api"

async def fetch_dart_disclosure(api_key: str, bgn_de: str, end_de: str):
    """공시 목록 조회."""
    params = {
        "crtfc_key": api_key,
        "bgn_de": bgn_de,  # 시작일 YYYYMMDD
        "end_de": end_de,
        "page_count": 100,
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{DART_BASE}/list.json", params=params)
        return r.json().get("list", [])
```

### Telegram Adapter

`python-telegram-bot` 또는 `telethon` 사용. Telethon이 채널 모니터링에 더 적합.

```python
from telethon import TelegramClient, events

# 진영님이 OpenClaw 작업 시 이미 익숙한 패턴
api_id = os.getenv("TG_API_ID")
api_hash = os.getenv("TG_API_HASH")

client = TelegramClient('dantalink', api_id, api_hash)

@client.on(events.NewMessage(chats=['속보채널1', '속보채널2']))
async def handler(event):
    await emit_trigger_event({
        "source": "TG",
        "title": event.raw_text[:200],
        "body": event.raw_text,
        "published_at": event.date,
    })
```

### WebSocket 연결 (Frontend ↔ Backend)

현재 GUI는 Mock으로 작동하지만, 실제 연결 시 다음과 같이 교체:

```javascript
// 현재 (Mock)
async function collectFromSource(source) {
  await sleep(500);
  return MOCK_EVENTS[source];
}

// 실제 (WebSocket 스트림)
const ws = new WebSocket('ws://localhost:8000/ws/events');

ws.onmessage = (msg) => {
  const evt = JSON.parse(msg.data);
  renderEvent({
    source: evt.source,
    title: evt.title,
    category: evt.category,
    keywords: evt.keywords,
    originalSource: evt.publisher,
    time: new Date(evt.published_at).toLocaleTimeString('ko-KR'),
  });
};

document.getElementById('btn-exec').addEventListener('click', () => {
  ws.send(JSON.stringify({
    action: 'start_scan',
    sources: Object.entries(STATE.sources).filter(([_, v]) => v).map(([k]) => k),
    keywords: STATE.keywords,
    timespan: STATE.timespan,
  }));
});
```

---

## 🧬 데이터 모델 (Stage 02 인계 형식)

수집된 이벤트는 다음 표준 형식으로 Stage 02 (매칭 후보 생성)에 전달된다.

```python
@dataclass
class TriggerEvent:
    event_id: str               # SHA256 해시 16자리
    source: EventSource         # GDELT | RSS | KRX | TG
    title: str                  # 헤드라인
    body: str                   # 본문 (최대 2000자)
    url: Optional[str]
    published_at: datetime      # UTC
    collected_at: datetime      # UTC
    category: EventCategory     # 휴리스틱 1차 분류
    keywords: list[str]         # 매칭된 키워드들
    entities: list[str]         # 인물·기관·지명 (NER)
    raw_payload: dict           # 원본 데이터 보존
```

JSON 직렬화 예시:

```json
{
  "event_id": "a7f3c92b8e1d4f56",
  "source": "gdelt",
  "title": "WHO declares PHEIC over Bundibugyo Ebola outbreak",
  "body": "...",
  "url": "https://www.reuters.com/...",
  "published_at": "2026-05-19T15:32:00+00:00",
  "collected_at": "2026-05-20T01:45:23+00:00",
  "category": "health",
  "keywords": ["WHO", "PHEIC", "에볼라", "분디부교"],
  "entities": ["WHO", "DRC", "Uganda", "Bundibugyo"],
  "raw_payload": { ... }
}
```

---

## 🚀 실행 방법

### 현재 상태 (브라우저 단독)
```bash
# 그냥 HTML 파일을 브라우저에서 열기
open DantaLink_데이터수집기.html
```

### 백엔드 연결 후 (다음 단계)
```bash
# 백엔드 서버
cd backend
uv venv && source .venv/bin/activate
uv pip install fastapi uvicorn httpx feedparser telethon python-dotenv
uvicorn main:app --reload --port 8000

# 프론트엔드는 동일 (WebSocket URL만 환경변수로)
```

---

## 📁 파일 구조 (향후 백엔드/프론트엔드 분리 시 계획)

> ⚠️ **현재 실제 구조는 단일 `dantalink/` Python 패키지**(README.md 참고). 아래는 GUI를 본격 도입하여 FastAPI 백엔드 + HTML 프론트엔드로 분리할 때의 목표 구조다. Stage 02~05 모듈이 준비되면 점진적으로 이 구조로 이행할 수 있다.

```
DantaLink/
├── frontend/
│   ├── data_collector.html          # ← 현재 docs/ 에 있음
│   ├── match_generator.html         # Stage 02 (예정)
│   ├── signal_validator.html        # Stage 03 (예정)
│   ├── position_sizer.html          # Stage 04 (예정)
│   └── exit_manager.html            # Stage 05 (예정)
├── backend/
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseCollector ABC
│   │   ├── gdelt.py
│   │   ├── rss.py
│   │   ├── dart.py                  # 금감원 전자공시 (구 krx.py)
│   │   └── telegram.py
│   ├── classifier/
│   │   ├── heuristic.py             # 키워드 사전 기반
│   │   └── llm.py                   # Claude/Qwen 분류기
│   ├── models.py                    # TriggerEvent 등 데이터 모델
│   ├── main.py                      # FastAPI 엔트리
│   └── config.py
├── shared/
│   └── design-tokens.css            # HOBIS 디자인 시스템
└── docs/
    └── DantaLink_방법론.md
```

---

## ✅ 다음 단계 (Stage 02 작업 예고)

진영님이 맥북으로 옮긴 후 데이터 수집 결과를 이 세션으로 가져오면, 다음을 함께 작업할 수 있다:

1. **수집된 이벤트의 매칭 후보 생성**
   - Layer A: 음운 매칭 (Phonological)
   - Layer B: 카테고리 매칭 (Semantic)
   - Layer C: 약한 연결 매칭 (Weak Tie)

2. **한국 종목 DB 구축**
   - KRX 전체 종목 + 자회사 + 계열사 사명 데이터
   - 사명에서 추출한 음절 인덱스

3. **신뢰도 점수화 모듈**
   - 음운+카테고리 동시 매칭 시 0.55
   - 단일 매칭 시 0.30~0.40
   - LLM 검증 단계 추가 시 가중치 보정

4. **Stage 02 GUI** (Match Generator)
   - 동일한 HOBIS 디자인 시스템 계승
   - 좌측: 들어온 이벤트, 중앙: 매칭 시각화, 우측: 종목 후보 리스트

---

*DantaLink · SL Corporation / SeouLink*
*Draft v0.1 · Operator: 진영*
