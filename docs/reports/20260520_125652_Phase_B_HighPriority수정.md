# Phase B — Day 1 High Priority 수정

- **시작**: 2026-05-20 12:52:00 (Phase A QC#1 통과 직후)
- **종료**: 2026-05-20 12:56:52
- **소요**: 약 5분
- **작성자**: Claude Code (윈도우 세션)

---

## 1. 적용된 변경 (5건)

### H1. KRX → DART rename
**문제**: `KRXCollector`가 실제로는 DART(금감원 전자공시) API를 호출하는데 이름이 KRX(한국거래소)로 명명되어 향후 진짜 KRX 시세 API 추가 시 충돌 위험.

**변경 내용**:
1. **신규 파일**: `dantalink/collectors/dart.py` — krx.py 내용 복제 + 클래스명 `DARTCollector`로 변경, `source = EventSource.DART`
2. **기존 파일**: `dantalink/collectors/krx.py` → deprecated alias 모듈로 축소 (subclass + `DeprecationWarning` 발생)
3. **EventSource enum 추가** (`dantalink/models/__init__.py`):
   ```python
   class EventSource(str, Enum):
       GDELT = "gdelt"
       RSS = "rss"
       DART = "dart"        # 신규
       KRX = "krx"          # Deprecated alias (backward compat용)
       TELEGRAM = "telegram"
   ```
4. **`dantalink/collectors/__init__.py`**: `DARTCollector` 추가 export, KRXCollector는 deprecated 표시 유지
5. **`dantalink/cli.py`**:
   - `from .collectors import KRXCollector` → `DARTCollector`
   - `if "krx" in sources:` → `if "dart" in sources or "krx" in sources:` (별칭 호환)
   - `--sources` 기본값 `gdelt,rss,krx` → `gdelt,rss,dart`
6. **`README.md` 트리 구조**: `dart.py` 추가, `krx.py`에 deprecated 메모

**Backward compatibility**:
- 외부 코드에서 `from dantalink.collectors import KRXCollector` 여전히 동작 (DeprecationWarning 발생)
- 기존 JSON 출력에 `"source": "krx"`가 있어도 `EventSource.KRX`로 역직렬화 가능
- CLI 사용자가 `--sources krx` 입력 시 DARTCollector로 자동 매핑

### H2. test_classifier.py 분디부조 오타
**문제**: `tests/test_classifier.py:20` `"분디부조"` (오타) — 정답은 **분디부교**(Bundibugyo, 우간다 지명). 분류기 키워드 사전과 방법론.md 모두 "분디부교"로 표기됨.

**변경**:
```python
# Before
text = "분디부조 에볼라 백신 임상시험 WHO 검토 착수"
assert cat == EventCategory.HEALTH
assert "에볼라" in kws
assert "백신" in kws
assert "WHO" in kws

# After
text = "분디부교 에볼라 백신 임상시험 WHO 검토 착수"
assert cat == EventCategory.HEALTH
assert "분디부교" in kws          # ← 신규 단정 추가
assert "에볼라" in kws
assert "백신" in kws
assert "WHO" in kws
```

**의미**: 분류기 사전의 "분디부교" 키워드가 실제로 매칭되는지 명시적으로 검증 (기존엔 의도는 검증 안 됨).

### H4. CLI/Telegram 일관성
**결정**: 옵션 A 채택 — Telegram은 batch CLI 미지원, 별도 데몬으로 분리 예정.

**근거**: `telegram.py` 모듈 docstring에 이미 "실시간 모드는 향후 별도 데몬으로 분리 예정"이라 명시됨. 다른 수집기(GDELT/RSS/DART)는 pull 방식인데 Telegram만 push라 패턴 충돌. 강제로 batch에 끼우면 CLI 사용자가 자격 증명·세션 파일까지 갖춰야 해서 진입 장벽 상승.

**변경**: `README.md` 환경변수 섹션에 명시적 안내 추가
```
> Telegram 수집기는 push 방식(실시간 채널 모니터링)이라 다른 수집기와 흐름이 달라,
> `dantalink scan` 명령에 포함되지 않습니다. 라이브러리로 직접 호출하거나
> 향후 별도 데몬 프로세스로 분리할 예정입니다.
```

### H5. 데이터수집기_문서.md 구조 명확화
**문제**: `docs/DantaLink_데이터수집기_문서.md`의 "파일 구조 (계획)" 섹션이 현재 `dantalink/` 단일 패키지 구조와 달라 보였음. 실제로는 GUI 도입 시 frontend/backend 분리 계획이었음.

**변경**: 섹션 제목 `## 📁 파일 구조 (계획)` → `## 📁 파일 구조 (향후 백엔드/프론트엔드 분리 시 계획)`, 도입부에 명시:
> ⚠️ **현재 실제 구조는 단일 `dantalink/` Python 패키지**(README.md 참고). 아래는 GUI를 본격 도입하여 FastAPI 백엔드 + HTML 프론트엔드로 분리할 때의 목표 구조다. Stage 02~05 모듈이 준비되면 점진적으로 이 구조로 이행할 수 있다.

또한 트리 내 `krx.py` → `dart.py` (구 krx.py) 로 표기 동기화 (H1 일치).

### .gitignore — dantalink.zip 정리
**문제**: 프로젝트 루트에 검토용 zip(66KB)이 git 추적 후보로 잔존.

**변경**: `.gitignore`에 추가
```
# Packaged exports (Claude 챗 검토용 zip 등)
dantalink.zip
*.zip
```

물리적 삭제는 보류 (검토 자료 보존 + 차후 결정).

---

## 2. 영향 받지 않은 영역 (의도된 미변경)

| 영역 | 사유 |
|------|------|
| `dantalink/pipeline.py` | 변경 불필요 (수집기 추상화로 인해 KRX→DART 영향 흡수) |
| `dantalink/classifier/` | 변경 불필요 (분류기는 source agnostic) |
| `examples/basic_scan.py` | GDELT+RSS만 사용, DART 미포함 |
| `tests/test_models.py` | EventSource 추가 영향 없음 (KRX 직접 참조 없음) |
| `CLAUDE.md` | 일관성 OK, 변경 보류 |

---

## 3. 변경 파일 요약

| 파일 | 변경 유형 | 라인 수(증감) |
|------|---------|------|
| `dantalink/collectors/dart.py` | NEW | +166 |
| `dantalink/collectors/krx.py` | 전면 교체 (deprecated alias) | -130 / +24 |
| `dantalink/collectors/__init__.py` | EDIT | +2 / -0 |
| `dantalink/models/__init__.py` | EDIT (enum +1, 코멘트) | +5 / -1 |
| `dantalink/cli.py` | EDIT (3곳) | +4 / -3 |
| `tests/test_classifier.py` | EDIT (1줄 오타 + 1줄 단정 추가) | +2 / -1 |
| `README.md` | EDIT (트리 + 환경변수 메모) | +5 / -1 |
| `docs/DantaLink_데이터수집기_문서.md` | EDIT (구조 섹션 명확화) | +4 / -2 |
| `.gitignore` | EDIT (zip 패턴 추가) | +4 / -0 |

---

## 4. 다음 단계 (품질검사 #2 진입 조건)

- pytest 13건(기존) + 분디부교 추가 단정 모두 통과 확인
- import 오류 없음 (`from dantalink import ...`)
- DeprecationWarning이 KRXCollector 인스턴스화 시에만 발생 (모듈 import 시점 X)

### 품질검사 #2 항목
- [ ] `pip install -e ".[dev]"` 정상 종료
- [ ] `python -c "from dantalink import ...; from dantalink.collectors import DARTCollector, KRXCollector"` 무오류
- [ ] `pytest tests/ -v` → 13 passed (or 13 passed + warnings)
- [ ] `python -m dantalink.cli --help` 정상 출력
- [ ] CLI `--sources dart` 와 `--sources krx` 모두 작동 (실제 호출 안 해도 인자 파싱은)
