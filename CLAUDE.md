# CLAUDE.md — DantaLink 작업 프로토콜

> 이 파일은 Claude Code 세션에서 일관된 작업을 위한 컨텍스트 문서입니다.
> MOAT(Mother Of All Thoughts) 시스템과 호환되도록 작성되었습니다.

---

## 🎯 프로젝트 정체성

**DantaLink** = "단타 + Link" · SeouLink 산하 행동재무 기반 단타 발굴 시스템.

### 한 줄 요약
한국 시장의 음운/카테고리 매칭으로 발생하는 단기 모멘텀을 시스템적으로 포착하는 도구.

### 학술적 근거
- 카너먼·트버스키의 대표성/가용성 휴리스틱
- Rashes (2001) 이름 유사성 효과
- Da, Engelberts, Gao (2011) 주목 기반 거래
- Barber & Odean (2008) 주목 기반 매수
- 자세한 내용: `docs/DantaLink_방법론.md`

### 비즈니스 단계
1. ✅ Python 백엔드 검증 (현재 작업 단계)
2. ⏳ iPhone 앱 (TestFlight 알파)
3. ⏳ iOS / Android 동시 출시

---

## 📁 프로젝트 구조

```
dantalink/
├── CLAUDE.md                          # 이 파일 (작업 프로토콜)
├── README.md                          # 일반 사용자용 README
├── pyproject.toml                     # 패키지 설정
├── .env.example                       # 환경변수 템플릿
│
├── dantalink/                         # 메인 패키지
│   ├── __init__.py
│   ├── cli.py                         # CLI 진입점
│   ├── pipeline.py                    # 오케스트레이션
│   ├── models/                        # TriggerEvent, EventCategory
│   ├── classifier/                    # 휴리스틱 분류기
│   └── collectors/                    # 수집기 (GDELT/RSS/KRX/Telegram)
│
├── docs/                              # 설계 문서
│   ├── DantaLink_방법론.md            # 전체 방법론 (Stage 1~5)
│   ├── DantaLink_시각화.html          # 방법론 인터랙티브 시각화
│   ├── DantaLink_데이터수집기.html    # Stage 01 GUI 프로토타입
│   └── DantaLink_데이터수집기_문서.md # 데이터 수집기 디자인 가이드
│
├── examples/                          # 사용 예시
│   └── basic_scan.py
│
└── tests/                             # 단위 테스트 (pytest)
    ├── test_classifier.py
    └── test_models.py
```

---

## 🛠️ 개발 환경

### 의존성
- Python ≥ 3.10
- httpx (비동기 HTTP)
- feedparser (RSS 파싱)
- telethon (선택, Telegram)
- pytest, pytest-asyncio (테스트)

### 설치
```bash
pip install -e ".[dev]"           # 개발용
pip install -e ".[dev,telegram]"  # Telegram 포함
```

### 환경변수
- `DART_API_KEY`: 금융감독원 전자공시 API 키
- `TG_API_ID`, `TG_API_HASH`: Telegram API (선택)

---

## 📐 코딩 규칙 (Claude 작업 시 준수)

### 일반 원칙
1. **타입 힌트 필수**: Python 3.10+ 신규 문법 사용 (`list[str]`, `X | None`)
2. **dataclass 우선**: 데이터 모델은 `@dataclass` 사용
3. **async/await 일관성**: I/O는 모두 비동기, blocking 작업은 `asyncio.to_thread`
4. **로깅 사용**: print 대신 `self.logger.info/error/exception` 사용
5. **에러 격리**: 단일 컴포넌트 실패가 전체 파이프라인을 막지 않도록 `safe_fetch` 패턴

### 네이밍 컨벤션
- 모듈: snake_case (`gdelt.py`)
- 클래스: PascalCase (`GDELTCollector`)
- 함수/변수: snake_case (`fetch_events`)
- 상수: UPPER_SNAKE (`GDELT_BASE_URL`, `CATEGORY_KEYWORDS`)
- 비공개: `_underscore_prefix`

### 데이터 모델 변경 시
- `TriggerEvent`는 **모든 수집기의 표준 출력** → 변경 시 모든 collector 동기 업데이트
- `EventCategory`/`EventSource` enum 변경 시 `classifier/`도 같이 업데이트
- 직렬화 (`to_dict`) 호환성 유지 — iOS 앱에서 동일 JSON 스키마 사용 예정

### 새 수집기 추가 시 체크리스트
- [ ] `BaseCollector` 상속
- [ ] `source: EventSource` 클래스 변수 정의
- [ ] `async def fetch() -> list[TriggerEvent]` 구현
- [ ] 본문 예외 처리: 외부 API 실패는 빈 리스트 반환 + 로깅
- [ ] `collectors/__init__.py`에 export 추가
- [ ] `tests/`에 mock 기반 단위 테스트 추가
- [ ] CLI에 `--sources` 옵션 추가
- [ ] README 업데이트

---

## 🚀 자주 쓰는 명령

### 테스트
```bash
pytest tests/ -v                  # 전체
pytest tests/test_classifier.py   # 모듈별
pytest -k "test_classify_health"  # 특정 테스트
```

### 린트
```bash
ruff check dantalink/
ruff format dantalink/
```

### 실행
```bash
# CLI
dantalink scan --keywords "에볼라,AI" --timespan 24h

# 예시 스크립트
python examples/basic_scan.py

# 모듈 직접 호출
python -m dantalink.cli scan --keywords "WHO"
```

---

## 🎨 디자인 시스템

iOS 앱과 GUI는 **HOBIS 디자인 시스템 (Terran Console Aesthetic)** 을 계승한다.

### 핵심 토큰
| 토큰 | 값 | 용도 |
|------|-----|------|
| `--terran` | `#ffb627` | 시그니처 옐로우 (액션, 강조) |
| `--cyan` | `#4ecdc4` | HUD 액센트 |
| `--red` | `#ff3a3a` | 경고/긴급 |
| `--green` | `#4ade80` | 정상 작동 |
| `--bg-void` | `#050810` | 최하층 배경 |
| `--bg-panel` | `#131820` | 패널 배경 |

### 폰트
- **본문/콘솔**: JetBrains Mono
- **디스플레이**: Orbitron (각진 SF 미학)

### 인터랙션
- 펄스 LED (정상 작동 인디케이터)
- 스캔라인 오버레이 (CRT 효과)
- 다이아몬드 클립 버튼 (`clip-path: polygon`)
- 글로우 box-shadow (액티브 상태)

**참고 파일**: `docs/DantaLink_데이터수집기.html`

---

## 🔄 5단계 로드맵 (방법론)

| Stage | 모듈 | 현재 상태 |
|-------|------|----------|
| 01. 트리거 감지 | `collectors/` | ✅ 구현 완료 (RSS 8 피드, GDELT, DART) |
| 02. 매칭 후보 생성 | `matchers/` | 🟡 1차 구현 완료 (Layer A/B), 외국 인명 패턴 등 정교화 필요 |
| 03. 진입 신호 검증 | `filters/` (예정) | ⏳ |
| 04. 포지션 사이징 | `sizing/` (예정, Kelly 1/4) | ⏳ |
| 05. 청산 규칙 | `exit/` (예정) | ⏳ |

상세 내용: `docs/DantaLink_방법론.md`

---

## 🔁 작업 워크플로우 (필수 준수)

> ⚠️ **이 워크플로우는 모든 세션(윈도우/맥북/CI)에서 동일하게 적용된다.** Claude는 매 작업 단위 종료 시 아래 6단계를 반드시 거친 후에만 다음 작업을 시작한다. 사용자 명시 요청이 없어도 자동 수행.

### 작업 단위 정의
- **작업 단위 (Work Unit)** = 사용자 1개 요청에 대응하는 1개 Phase 또는 Phase 내 하위 Step
- 예시:
  - "H1 KRX→DART rename" = 1 작업 단위
  - "matchers 모듈 6 파일 작성" = 1 작업 단위
  - "Layer A 음운 매칭 구현" = 1 작업 단위

### 워크플로우 6단계

```
[0] 결정 보고서 (큰 설계 결정인 경우만)
    docs/reports/YYYYMMDD_HHmmss_결정_{주제}.md — 옵션 비교 + 사용자 확인
        ↓
[1] 작업 실행 (코드/문서 변경)
        ↓
[2] 품질검사 실행 (자동 검증 스크립트)
        ↓
[3] 품질검사 보고서 작성 (docs/reports/YYYYMMDD_HHmmss_QC_{번호}_{제목}.md)
        ↓
[4] 시행착오·노하우 보고서 작성 또는 갱신
    - 새 함정 발견 시: 신규 보고서 (docs/reports/YYYYMMDD_HHmmss_시행착오_{주제}.md)
    - 기존 함정 재발견 시: 가장 최신 시행착오 보고서에 추가 섹션
        ↓
[5] 다음 작업 진입 (또는 사용자 확인 단계)
```

### [0] 결정 보고서 — 큰 설계 결정 시 사전 의무 (2026-05-20 신규)

> ⚠️ **사용자가 명시한 작은 요청이라도 구현 방식이 여러 갈래일 수 있다면 옵션을 사용자에게 제시한 후 결정 받는다.** 자율적으로 큰 결정을 내려서는 안 된다 (사용자 의도 오해석 위험 + 향후 운영 부담 발생).

**큰 설계 결정의 정의** (다음 중 하나라도 해당하면 [0] 의무):
- 새 모듈/패키지 추가 (예: `matchers/`, `server/`)
- 기존 코드의 알고리즘 포팅 (Python ↔ JS, 언어 간 동기화 부담 발생)
- 데이터 이중 보관 (예: CSV → JSON 변환, DB → dump)
- 외부 의존성 추가 (`pip install …`, `npm install …`, CDN 의존)
- 데이터베이스 스키마 변경
- 빌드/배포 구조 변경 (GitHub Pages 활성화, Docker 도입, CI/CD)
- 권한·인증 구조 변경 (env var 신규, secret 도입)

**[0] 결정 보고서 형식** (`docs/reports/YYYYMMDD_HHmmss_결정_{주제}.md`):

```markdown
## 결정 사항
[무엇을 결정해야 하는가 — 사용자 요청 원문 + 가능한 해석]

## 옵션 비교
| 옵션 | 설명 | 구현 비용 | 운영 부담 | 사용자 의도 부합 | 비고 |
|------|------|---------|---------|--------------|------|
| A | … | ★☆☆☆☆ | 없음 | 70% | … |
| B | … | ★★★★☆ | 동기화 부담 | 95% | … |

## 권장안 및 근거
[하나 골라 + 근거 명시 + 트레이드오프 설명]

## 사용자 확인 요청
**AskUserQuestion으로 사용자에게 선택 요청** → 답변 받기 전까지 구현 진행 X
```

**진행 정책**:
- 결정 보고서 작성 → AskUserQuestion 호출 → 사용자 답변 → 그 시점부터 [1] 진입
- 답변 받지 못한 상태에서 자율 진행 금지
- 단, 사용자가 "알아서 진행", "권장안으로", "옵션 비교 생략하고 진행" 명시한 경우는 그대로 진행

**위반 시 회복 절차**:
1. 작업 중단 (이미 진행됐다면 그대로 두되 회고)
2. 회고 보고서 (`YYYYMMDD_HHmmss_회고_{주제}.md`) — 자기 비판 + 옵션 사후 비교 + 사용자 의해 분석
3. 누락된 [3] QC 보고서 보강 작성
4. 사용자에게 회고 보고 + 다음 단계 결정 요청

### 각 단계 산출물 (필수)

#### [2] 품질검사 — 다음 중 해당 항목 모두 실행
- 코드 변경 시: `pytest tests/ -v` 통과
- import 변경 시: `python -c "from dantalink import ...; from dantalink.collectors import ...; from dantalink.matchers import ..."` 무오류
- CLI 변경 시: `python -m dantalink.cli --help`, `dantalink scan --help`, `dantalink match --help` 정상
- 외부 API 사용 시: 라이브 호출 1회 (또는 mock) — 실패 시 차단 원인 분석
- JSON 산출물: 파일 존재 + `json.load()` 무오류 + 한글 정상

#### [3] 품질검사 보고서 형식 (`docs/reports/YYYYMMDD_HHmmss_QC_{번호}_{제목}.md`)
- 시각·대상 Phase·검사자 명시
- 검사 항목 표 (기대값 / 실측 / 판정 PASS|FAIL)
- 부가 검증 (인코딩, 호환성 등)
- **판정**: 종합 PASS/FAIL + 다음 단계 진입 승인 여부
- 미해결/유의 사항 명시

#### [4] 시행착오·노하우 보고서 (`docs/reports/YYYYMMDD_HHmmss_시행착오_{주제}.md`)
- 문제 진술 (현상)
- 진단 과정 (어떻게 발견했는지)
- 원인 분석
- 우회/해결 기법 (재사용 가능한 형태로)
- 노하우 추출 (일반화)
- 식별자 부여 (`TRAP-{영역}-{번호}` 또는 `KNOW-{영역}-{번호}`)

### 적합/부적합 판정 기준

- **적합 (PASS)** → 다음 작업 자동 진입
  - 모든 자동 검증 항목 통과
  - 미해결 사항이 있어도 명시되어 있고 다음 단계 진입을 막지 않음

- **부적합 (FAIL)** → 개선 후 재검사 (자동 반복)
  - 자동 검증 실패 (pytest 깨짐, import 오류 등)
  - 또는 사용자 의도와 명백히 불일치

- **사용자 확인 필요** → 자동 진입 정지, 사용자 메시지 대기
  - 정책 결정 (점수 가중치, 시총 정책 등)
  - 사용자가 직접 보는 산출물 검증 (종목 후보 적합성)

### 파일명 컨벤션 (사용자 글로벌 지침 준수)

```
YYYYMMDD_HHmmss_{유형}_{제목}.md

유형 예시:
- Phase_A_파일정리
- QC_01_파일시스템
- H3_RSS_healthcheck
- 시행착오_노하우_정리
- 사용자_테스트_요청
- 다음분기_우선작업_{주제}
```

### 맥북 세션 인계 절차

1. `docs/reports/`의 최신 보고서 시간 역순 스캔
2. 가장 최근 "시행착오·노하우" 보고서를 먼저 읽어 함정 회피
3. "다음 분기 우선 작업" 보고서로 작업 우선순위 파악
4. "사용자 테스트 요청" 또는 사용자 마지막 메시지 확인
5. 위 워크플로우 5단계 적용하여 다음 작업 시작

---

## ⏭️ 다음 분기 우선 작업

> 이 섹션은 **현 작업 단위가 끝나고 다음 작업으로 진입할 때** 참조한다. 완료 시 ✅로 표시하고 다음 항목으로 이동.

### 🔴 우선순위 HIGHEST

- [ ] **외국 인명 패턴 인식 — 샘 알트먼 → 샘표 매칭**
  - 상세: `docs/reports/20260520_134506_다음분기_우선작업_외국인명패턴.md`
  - 대상: `dantalink/matchers/phonological.py`
  - 핵심: `r"[가-힣]{1,2}\s+[가-힣]{2,4}"` 패턴 우선 추출 → 1자 토큰 페널티 제외
  - 기대: 시연 시 샘표/샘표식품이 Top 5 진입

### 🟡 우선순위 HIGH

- [ ] **GUI 라이브 백엔드 연결**
  - 현재: 정적 JSON 로드 (events_*.json, matches_*.json)
  - 다음: FastAPI 백엔드 + WebSocket으로 실시간 scan/match 트리거
  - 대상: `dantalink/server/` 신규 (FastAPI 엔트리)

- [ ] **GDELT 맥북 IP 재검증**
  - 현재: 윈도우 IP 일시 차단 (코드 fix는 완료)
  - 다음: 맥북에서 라이브 수집 1회 → 5.5초 sleep 적정성 확인

- [ ] **Layer C — 약한 연결 매칭 (Weak Tie)**
  - "AI" → "에이아이"/"인공지능" 한영 변환
  - 사전 수동 큐레이션 또는 LLM 호출

### 🟢 우선순위 MEDIUM

- [ ] **SQLite persistence (M1)**: `events.db` — `event_id` PK, cross-session dedup
- [ ] **GDELT/DART rate limit retry (M2)**: exponential backoff
- [ ] **multi-source corroboration (M5)**: 동일 사건 다중 소스 누적 가중
- [ ] **collectors/* 단위 테스트**: mock httpx response, mock feedparser
- [ ] **KRX 섹터/테마(WICS/FICS) 통합**: Layer B 정교화

### 🔵 우선순위 LOW (장기)

- [ ] LLM 분류기 단계 (Claude API / 로컬 Qwen3.5)
- [ ] Stage 03 진입 신호 검증 (`filters/`)
- [ ] Stage 04 포지션 사이징 (`sizing/`, Kelly 1/4)
- [ ] Stage 05 청산 규칙 (`exit/`)
- [ ] 페이퍼 트레이딩 자동화 + 백테스트 인프라

---

## 🚨 절대 금지 사항

1. **자동 매수 코드 활성화 금지** — 현재 단계는 종목 발굴만. 매수/매도 API 호출은 사용자 명시적 승인 후에만.
2. **API 키 하드코딩 금지** — 항상 환경변수 또는 `.env` 사용
3. **단일 거래 자본 5% 초과 금지** — Kelly 1/4 공식이 권장하는 최대치
4. **종토방·게시판 글쓰기 자동화 금지** — 시장 조작 우려, 법적 회색지대

---

## 📚 참고 문서

- `docs/DantaLink_방법론.md` — 학술 근거 + 5단계 프레임워크
- `docs/DantaLink_시각화.html` — Kelly 공식 수식 시각화 (MathJax)
- `docs/DantaLink_데이터수집기.html` — Stage 01 GUI 프로토타입 (Mock)
- `docs/DantaLink_종목추출_GUI.html` — Stage 02 종목 추출 결과 GUI (matches_*.json 시각화)
- `README.md` — 일반 사용자용 (설치/사용법)
- `docs/reports/` — 모든 Phase·QC·시행착오·플랜 보고서 (`YYYYMMDD_HHmmss_*.md`)
  - 시간순 정렬, 맥북 세션 인계 시 가장 먼저 참조

---

## 🔗 SeouLink 생태계 위치

DantaLink는 다음 SeouLink 프로젝트들과 함께 운영된다:

- **HOBIS** — 방사선 방호 (디자인 시스템 원본)
- **CardioLink** — BLE ECG 모니터링
- **HornetLink** — 드론 플랫폼
- **StudioLink** — 카메라 + 비디오 편집
- **DantaLink** — 단타 발굴 (현재) ⬅️

공통 네이밍: `~~Link`

---

*최종 업데이트: 2026.05.20 (작업 워크플로우 + 다음 분기 우선 작업 + GUI 추가)*
*작성자: 진영 × Claude*
