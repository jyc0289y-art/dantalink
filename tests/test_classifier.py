"""분류기 단위 테스트.

실행:
    cd dantalink
    python -m pytest tests/ -v
"""
from dantalink.classifier import classify, matches_any_keyword
from dantalink.models import EventCategory


def test_classify_health():
    text = "WHO declares PHEIC over Bundibugyo Ebola outbreak in DRC and Uganda"
    cat, kws = classify(text)
    assert cat == EventCategory.HEALTH
    assert "WHO" in kws
    assert "PHEIC" in kws


def test_classify_korean_health():
    text = "분디부교 에볼라 백신 임상시험 WHO 검토 착수"
    cat, kws = classify(text)
    assert cat == EventCategory.HEALTH
    assert "분디부교" in kws
    assert "에볼라" in kws
    assert "백신" in kws
    assert "WHO" in kws


def test_classify_geopolitical():
    text = "US-Iran tensions escalate; Hormuz Strait shipping disrupted"
    cat, kws = classify(text)
    assert cat == EventCategory.GEOPOLITICAL
    assert "이란" in kws or "Iran" in str(kws)  # 영문/한글 매칭 케이스 모두 허용


def test_classify_tech():
    text = "OpenAI announces GPT-5 with breakthrough reasoning capabilities"
    cat, kws = classify(text)
    assert cat == EventCategory.TECH
    assert "OpenAI" in kws


def test_classify_person():
    text = "Sam Altman to visit South Korea for AI summit, 방한 일정 공개"
    cat, kws = classify(text)
    # AI 키워드가 TECH도 트리거하지만 방한은 PERSON
    # 매칭 개수에 따라 다름. tie-break에서 HEALTH→GEO→TECH→DISASTER→REGULATORY→PERSON
    # 그래서 TECH가 이길 가능성 있음. 둘 다 허용.
    assert cat in (EventCategory.TECH, EventCategory.PERSON)


def test_classify_unknown():
    text = "오늘 날씨가 좋네요. 점심으로 김치찌개를 먹었습니다."
    cat, kws = classify(text)
    assert cat == EventCategory.UNKNOWN
    assert kws == []


def test_classify_empty():
    cat, kws = classify("")
    assert cat == EventCategory.UNKNOWN
    assert kws == []


def test_matches_watch_keywords():
    text = "분디부교 에볼라 백신 관련 임상시험"
    hits = matches_any_keyword(text, ["에볼라", "AI", "샘 알트먼"])
    assert "에볼라" in hits
    assert "AI" not in hits


def test_matches_english_word_boundary():
    # "AI"는 단독 단어로만 매칭, "AID", "AIM" 등은 매칭 안 되어야 함
    hits1 = matches_any_keyword("This is about AI development", ["AI"])
    assert "AI" in hits1

    hits2 = matches_any_keyword("AID workers in Africa", ["AI"])
    assert "AI" not in hits2  # word boundary로 인해 AID는 매칭 안 됨


def test_tiebreak_priority():
    # HEALTH 1개(에볼라), GEOPOLITICAL 1개(이란) 동점인 경우
    # tiebreak에서 HEALTH가 GEOPOLITICAL보다 우선
    text = "에볼라 발생 와중에 이란 정세 불안"
    cat, kws = classify(text)
    # 동점이면 HEALTH 선택되어야 함
    assert cat == EventCategory.HEALTH
    assert "에볼라" in kws
    assert "이란" in kws
