# DantaLink: 행동재무 기반 한국시장 매매 방법론

> SeouLink 산하 신규 프로젝트 설계 문서
> 작성일: 2026년 5월 20일
> 작성자: 진영 × Claude

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [핵심 가설과 학술적 배경](#2-핵심-가설과-학술적-배경)
3. [세금 체계 정리](#3-세금-체계-정리)
4. [5단계 방법론 프레임워크](#4-5단계-방법론-프레임워크)
5. [시스템 아키텍처](#5-시스템-아키텍처)
6. [iOS 통합 전략](#6-ios-통합-전략)
7. [리스크 관리](#7-리스크-관리)
8. [용어집](#8-용어집)
9. [참고 문헌](#9-참고-문헌)

---

## 1. 프로젝트 개요

### 1.1 배경

한국 주식시장에는 펀더멘털 분석으로는 설명되지 않는 매매 패턴이 빈번하게 발생한다. 대표 사례:

- **아이진 급등 (2026.05)**: WHO의 분디부교 에볼라 PHEIC 선포 직후, 분디부교 백신 파이프라인이 없음에도 "백신주" 카테고리 매핑만으로 급등
- **샘표 급등 (반복)**: 샘 알트먼 OpenAI CEO 방한 시마다 사명의 첫 음절 일치만으로 주가 변동

이러한 현상은 우연이 아니라 인간의 인지 편향과 한국 시장의 구조적 특성이 결합된 **체계적 패턴**이다.

### 1.2 목표

- 인지 편향 기반 단기 매매 기회를 시스템적으로 포착
- 진영님의 직관을 검증 가능한 알고리즘으로 정형화
- SL Corporation/SeouLink 인프라와 통합된 자동화 시스템 구축

---

## 2. 핵심 가설과 학술적 배경

### 2.1 핵심 가설

> 한국 시장의 개인투자자 비중과 한국어 음운 체계의 특성상 외국 고유명사와 한국 종목명이 우연히 겹치는 빈도가 높으며, 정보 전파 속도가 극단적으로 빠르다. 따라서 음운/카테고리 매칭이 펀더멘털보다 단기 주가를 더 강하게 견인한다.

### 2.2 인지 매칭의 정교함 스펙트럼

```
[정교함 ↑]
│
│ ┌─ 펀더멘털 분석 (실제 실적·재무)
│ ├─ 산업 인과 분석 (대체재·보완재)
│ ├─ 카테고리 매핑 ←── 아이진 (백신 박스)
│ ├─ 의미적 점화 (개념 연상)
│ ├─ 이름 유사성 ←── 샘표 (음절 매칭)
│ └─ 티커 혼동 (가장 원시적)
│
[정교함 ↓]
```

### 2.3 주요 학술 개념

| 개념 | 영문명 | 핵심 주장 | 대표 학자 |
|------|--------|----------|----------|
| 대표성 휴리스틱 | Representativeness Heuristic | 표면적 유사성에 기반한 판단 | Kahneman & Tversky (1972) |
| 가용성 휴리스틱 | Availability Heuristic | 떠올리기 쉬운 정보로 결정 | Kahneman & Tversky (1973) |
| 제한된 주의력 | Limited Attention | 인지자원 부족으로 표면 신호만 처리 | Hirshleifer & Teoh (2003) |
| 노이즈 트레이더 | Noise Trader Theory | 비펀더멘털 정보로 거래 | Fisher Black (1986) |
| 거친 사고 | Coarse Thinking | 세상을 거친 범주로 분류 | Mullainathan et al. (2008) |
| 의미적 점화 | Semantic Priming | 연관 개념 자동 활성화 | 인지심리학 |
| 음운적 점화 | Phonological Priming | 소리 기반 인지 활성화 | 인지심리학 |
| 이름 유사성 효과 | Name Similarity Effect | 티커·사명 유사성이 주가에 영향 | Rashes (2001) |
| 인지적 유창성 | Cognitive Fluency | 발음 쉬운 종목이 더 매수됨 | Alter & Oppenheimer (2006) |
| 주목 기반 거래 | Attention-Driven Trading | 검색량 급증이 단기 수익률 예측 | Da, Engelberts, Gao (2011) |

### 2.4 진영님 사례 분석

**아이진 케이스 (카테고리 매핑)**
- 트리거: WHO 분디부교 에볼라 PHEIC 선포
- 매칭 논리: "에볼라" → "백신" → "백신주 카테고리" → "아이진"
- 실제 분디부교 백신 파이프라인 보유 여부와 무관

**샘표 케이스 (음운 매칭)**
- 트리거: 샘 알트먼 OpenAI CEO 방한
- 매칭 논리: "Sam" 음절 → "샘표" 사명
- 사업적 연관성 0, 순수 기표(signifier) 매칭

---

## 3. 세금 체계 정리

### 3.1 양도소득세

| 구분 | 양도세 부과 여부 | 세율 |
|------|----------------|------|
| 상장주식 - 소액주주 - 장내거래 | ❌ 비과세 | - |
| 상장주식 - 대주주 | ✅ 과세 | 22~33% |
| 상장주식 - 장외거래 | ✅ 과세 | 22% 등 |
| 비상장주식 | ✅ 과세 | 22% 등 |

### 3.2 대주주 기준 (2026년)

- **코스피**: 종목당 지분 1% 이상 OR 보유액 50억 원 이상
- **코스닥**: 종목당 지분 2% 이상 OR 보유액 50억 원 이상
- **코넥스**: 종목당 지분 4% 이상 OR 보유액 50억 원 이상

### 3.3 종합소득세 (배당소득 관련)

| 구간 | 과세 방식 |
|------|----------|
| 배당소득 연 2,000만 원 이하 | 분리과세 15.4% (원천징수로 종결) |
| 배당소득 + 이자소득 연 2,000만 원 초과 | 금융소득종합과세 → 누진세 (최고 49.5%) |

### 3.4 증권거래세

- 코스피: 0.18% (농특세 0.15% 포함)
- 코스닥: 0.18%
- 매도 시 자동 원천징수

### 3.5 진영님 상황 정리

- 매매차익만 노릴 경우 → 종소세 무관
- 배당소득 많을 경우 → 2,000만 원 선 주의
- **SL Corporation 법인 소득과 합산 시 누진세 폭발 가능**

---

## 4. 5단계 방법론 프레임워크

### Stage 1: 트리거 이벤트 감지

| 트리거 유형 | 감지 소스 | 예시 |
|------------|----------|------|
| 국제 인물 방한/발언 | 연합뉴스, Reuters 실시간 | "샘 알트먼 방한" |
| WHO/CDC 비상사태 | WHO RSS, 질병관리청 | "분디부교 PHEIC" |
| 글로벌 지정학 이벤트 | 외신 속보 | "미국-이란 충돌" |
| 외신 신기술 발표 | TechCrunch, The Verge | "OpenAI 신모델" |
| 글로벌 재난/사고 | 로이터 알림 | "혼디우스호 한타바이러스" |

**기술 스택**
- News API, GDELT Project
- 텔레그램 채널 크롤링
- RSS 어그리게이터 + LLM 분류

### Stage 2: 매칭 후보군 생성

**Layer A: 음운 매칭 (Phonological)**
- 트리거 이름의 첫 1~2음절 추출
- 한국 종목명 DB 음절 매칭
- 예: "Sam Altman" → 샘표

**Layer B: 의미 카테고리 매칭 (Semantic)**
- 사건의 산업 카테고리 추출
- KRX 분류 종목 호출
- 예: "에볼라" → 백신/바이오

**Layer C: 약한 연결 매칭 (Weak Tie)**
- 모든 키워드 한국어 변환 검색
- 동음이의어, 동철자 포함
- 예: "AI" → "에이아이" "인공지능"

### Stage 3: 진입 신호 검증

| 필터 | 기준 |
|------|------|
| 시가총액 | 5,000억 이하 우선 |
| 유동성 | 일평균 거래대금 50억 이상 |
| 신용잔고율 | 5% 이하 |
| 차트 상태 | 60일선 위 + 거래량 2배 이상 |
| 공시 청정성 | 최근 7일 내 유증·CB 공시 없음 |

### Stage 4: 포지션 사이징 & 진입

**Kelly Criterion 변형 공식**
```
f* = (p × b - q) / b × 0.25

p = 매칭 신뢰도
  · 음운만: 0.30
  · 카테고리만: 0.40
  · 둘 다: 0.55
b = 예상 수익률 / 예상 손실률 (보통 2~3)
q = 1 - p
0.25 = 안전 마진 (Full Kelly의 1/4)
```

**진입 가이드**
- 단일 테마: 총 자본의 2~5%
- 분할 진입: 시초가 30% → 첫 눌림목 30% → 추세 확인 40%
- 물타기 절대 금지

### Stage 5: 청산 규칙

| 청산 조건 | 트리거 | 비율 |
|----------|--------|------|
| 목표가 1차 | +15% | 50% 청산 |
| 목표가 2차 | +25% | 추가 30%, 트레일링 20% |
| 트레일링 스탑 | 고점 -7% | 100% |
| 손절 | -5% | 100% |
| 시간 손절 | 5거래일 경과 | 100% |
| 모멘텀 소멸 | 후속 보도 끊김 | 즉시 |

---

## 5. 시스템 아키텍처

### 5.1 전체 구조

```
[데이터 수집 레이어]
├─ News API + GDELT (글로벌 이벤트)
├─ 네이버금융 크롤러 (한국 시장)
├─ KRX 공시 API
└─ 텔레그램 속보 채널

         ↓

[처리 레이어]
├─ LLM 분류기 (Claude API / 로컬 Qwen3.5)
│  ├─ 트리거 이벤트 추출
│  ├─ 음운 매칭 후보
│  └─ 카테고리 매칭 후보
├─ 종목 필터링 엔진 (Python)
└─ 신호 강도 점수화

         ↓

[디스패치 레이어]
├─ 텔레그램 봇 (즉시 푸시)
├─ iCloud 노트 (이력 보관)
├─ Mac 알림센터 (책상)
└─ 한국투자증권 API (자동매수, 선택)
```

### 5.2 진영님 기존 자산 활용

- **M5 Mac (32GB)**: 신호 감지 데몬 + LLM 분류기
- **Mac Studio (예정)**: 24/7 자동매매 엔진
- **Tailscale**: 원격 접근 보안 채널
- **로컬 Qwen3.5-397B-A17B**: 프라이버시 보존 분류
- **OpenClaw 텔레그램 봇 경험**: 즉시 적용 가능

---

## 6. iOS 통합 전략

### 6.1 직접 거래 가능 방법 정리

| 방법 | 난이도 | 속도 | 추천도 |
|------|--------|------|--------|
| iOS Shortcuts + REST API | 중 | 빠름 | ⭐⭐⭐⭐⭐ |
| Pythonista 3 (앱) | 중 | 중간 | ⭐⭐⭐ |
| 텔레그램 봇 → Mac 서버 | 낮음 | 매우 빠름 | ⭐⭐⭐⭐⭐ |
| AWS Lambda 우회 | 높음 | 빠름 | ⭐⭐ |

### 6.2 한국투자증권 REST API 핵심 정보

- **Base URL**: `https://openapi.koreainvestment.com:9443`
- **인증**: OAuth 2.0 (APP Key + APP Secret → Access Token)
- **토큰 유효기간**: 24시간
- **주문 코드**:
  - `01`: 시장가
  - `02`: 지정가
  - `03`: 조건부 지정가
  - `05`: 장전 시간외

### 6.3 iOS 단축어 흐름

```
[Siri "행동재무 매수"]
        ↓
[Shortcut: 종목 입력 요청]
        ↓
[Get Contents of URL]
  - POST openapi.koreainvestment.com:9443/...
  - Authorization: Bearer {token}
  - tr_id: TTTC0802U
        ↓
[Siri 음성 피드백: "○○ 매수 완료"]
```

### 6.4 최적 하이브리드 구조

```
[Tier 1: 강신호 자동매매]
Mac Studio 24/7 데몬
└─ 신뢰도 > 0.8일 때만 자동 실행

[Tier 2: 보조신호 수동승인]
Mac → 텔레그램 봇 → iPhone
└─ 인라인 버튼 승인 → 콜백 실행

[Tier 3: 외출 중 긴급매매]
iPhone Shortcut → KIS REST API
└─ Siri 음성 명령 지원
```

---

## 7. 리스크 관리

### 7.1 시스템 리스크

1. **그레이터 풀 게임**: 알고리즘화 진행 시 알파 소실
2. **백테스트 한계**: 과거 음운 매칭 데이터셋 부재
3. **법적 회색지대**: 종토방 글쓰기 + 매매 조합 회피 필수
4. **세금 변동 리스크**: 양도세 면제 폐지 논의 모니터링

### 7.2 운영자 개인 리스크

- **신체 컨디션 관리**: 자극적 단타 매매는 신체적 긴장을 유발할 수 있으므로 본인 건강 상태(혈압·심박 등)에 맞춰 매매 빈도와 강도 조절 필요
- **의사결정 피로**: 레버리지 ETF + 단타 병행 시 인지 부담 가중
- **약물 상호작용**: 신경계 영향이 있는 약물 복용 중인 경우 새 약물 추가 시 상호작용 재검토 필수

> ℹ️ 운영자별 구체적 의료 정보(현재 복용 약물, 측정 수치 등)는 내부 문서(`docs/internal/`)로 별도 관리한다. 외부 공유 시 노출 차단.

### 7.3 권장 시작 순서

1. **2주 페이퍼 트레이딩**: 직관 적중률 측정
2. **소규모 실전**: 자본의 1~2%로 검증
3. **시스템 자동화**: 검증된 패턴만 자동화
4. **자동매매 신중**: 사람 in-the-loop 원칙 유지

---

## 8. 용어집

### 8.1 행동재무·인지심리 용어

| 영어 용어 | 발음기호 | 한국어 의미 |
|----------|---------|------------|
| Heuristic | /hjʊˈrɪstɪk/ | 인지 단축법 |
| Representativeness Heuristic | /ˌreprɪzenˈteɪtɪvnəs hjʊˈrɪstɪk/ | 대표성 휴리스틱 |
| Availability Heuristic | /əˌveɪləˈbɪləti hjʊˈrɪstɪk/ | 가용성 휴리스틱 |
| Limited Attention | /ˈlɪmɪtɪd əˈtenʃən/ | 제한된 주의력 |
| Noise Trader Theory | /nɔɪz ˈtreɪdər ˈθɪəri/ | 소음 거래자 이론 |
| Coarse Thinking | /kɔːrs ˈθɪŋkɪŋ/ | 거친(투박한) 사고 |
| Semantic Priming | /sɪˈmæntɪk ˈpraɪmɪŋ/ | 의미적 점화 |
| Phonological Priming | /ˌfɒnəˈlɒdʒɪkəl ˈpraɪmɪŋ/ | 음운적 점화 |
| Name Similarity Effect | /neɪm ˌsɪməˈlærəti ɪˈfekt/ | 이름 유사성 효과 |
| Cognitive Fluency | /ˈkɒɡnətɪv ˈfluːənsi/ | 인지적 유창성 |
| Mental Accounting | /ˈmentl əˈkaʊntɪŋ/ | 정신적 회계 |
| Attention-Driven Trading | /əˈtenʃən ˈdrɪvən ˈtreɪdɪŋ/ | 주목 기반 거래 |
| Signifier | /ˈsɪɡnɪfaɪər/ | 기표 (소쉬르) |
| Signified | /ˈsɪɡnɪfaɪd/ | 기의 (소쉬르) |
| Behavioral Finance | /bɪˈheɪvjərəl ˈfaɪnæns/ | 행동재무학 |

### 8.2 주요 학자

| 학자 | 발음 | 업적 |
|------|------|------|
| Daniel Kahneman | /ˈdæniəl ˈkɑːnəmən/ | 노벨경제학상 2002 |
| Amos Tversky | /ˈeɪmɒs ˈtvɜːrski/ | 카너먼 공동연구자 |
| Richard Thaler | /ˈrɪtʃərd ˈθeɪlər/ | 노벨경제학상 2017 |
| Fisher Black | /ˈfɪʃər blæk/ | 노이즈 이론 |
| Andrei Shleifer | /ɑːnˈdreɪ ˈʃleɪfər/ | 비효율 시장 이론 |

---

## 9. 참고 문헌

1. Kahneman, D., & Tversky, A. (1972). "Subjective probability: A judgment of representativeness." *Cognitive Psychology*.
2. Kahneman, D., & Tversky, A. (1973). "Availability: A heuristic for judging frequency and probability." *Cognitive Psychology*.
3. Black, F. (1986). "Noise." *Journal of Finance*.
4. De Long, J. B., Shleifer, A., Summers, L. H., & Waldmann, R. J. (1990). "Noise Trader Risk in Financial Markets." *Journal of Political Economy*.
5. Rashes, M. S. (2001). "Massively Confused Investors Making Conspicuously Ignorant Choices (MCI-MCIC)." *Journal of Finance*.
6. Hirshleifer, D., & Teoh, S. H. (2003). "Limited attention, information disclosure, and financial reporting." *Journal of Accounting and Economics*.
7. Cooper, M. J., Dimitrov, O., & Rau, P. R. (2001). "A Rose.com by Any Other Name." *Journal of Finance*.
8. Alter, A. L., & Oppenheimer, D. M. (2006). "Predicting short-term stock fluctuations by using processing fluency." *PNAS*.
9. Mullainathan, S., Schwartzstein, J., & Shleifer, A. (2008). "Coarse Thinking and Persuasion." *Quarterly Journal of Economics*.
10. Barber, B. M., & Odean, T. (2008). "All That Glitters: The Effect of Attention and News on the Buying Behavior of Individual and Institutional Investors." *Review of Financial Studies*.
11. Da, Z., Engelberts, J., & Gao, P. (2011). "In Search of Attention." *Journal of Finance*.
12. Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
13. Shleifer, A. (2000). *Inefficient Markets: An Introduction to Behavioral Finance*. Oxford University Press.

---

*이 문서는 진영님과 Claude의 협업으로 작성된 DantaLink 프로젝트의 초기 설계 문서입니다.*
*SL Corporation / SeouLink 산하 프로젝트로 등록 검토 중.*
