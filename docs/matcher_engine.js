/**
 * DantaLink Matcher Engine (Client-Side)
 * ────────────────────────────────────────
 * Python `dantalink/matchers/*` 모듈의 JS 포팅 버전.
 * 브라우저에서 events.json → matches.json 변환을 직접 수행.
 *
 * 사용:
 *   const engine = new MatcherEngine();
 *   await engine.loadKRXDB('data/krx_stocks.json');
 *   const result = engine.match(events, { minMarcap: 100, maxMarcap: 5000 });
 *
 * 점수 체계 (방법론.md §4 Stage 4):
 *   Layer A — phonological:
 *     EXACT (token == name)         = 0.55
 *     first 2 syllables 일치        = 0.40
 *     first 1 syllable 일치         = 0.30  (1자 토큰은 ×0.7 페널티)
 *   Layer B — semantic:
 *     keyword substring 일치        = 0.50
 *     category theme 매칭           = 0.40
 */
(function (global) {
  'use strict';

  // ===== 분류기 사전 (Python classifier 그대로 옮김) =====
  const CATEGORY_KEYWORDS = {
    health: [
      "에볼라","바이러스","백신","감염병","팬데믹","변종","분디부교","한타바이러스",
      "코로나","독감","임상시험","WHO","CDC","PHEIC","질병관리청",
      "ebola","virus","vaccine","outbreak","pandemic","infection","clinical trial","FDA approval"
    ],
    geopolitical: [
      "전쟁","공격","미사일","제재","정상회담","휴전","이란","북한","러시아","우크라이나",
      "중동","이스라엘","관세","무역분쟁","수출규제","호르무즈",
      "war","attack","sanction","summit","tariff","ceasefire","missile","invasion",
      "Iran","North Korea","Russia","Ukraine","Israel","Hormuz","tension","tensions"
    ],
    tech: [
      "인공지능","반도체","메모리","온디바이스","양자컴퓨팅","로보틱스","자율주행","전기차",
      "OpenAI","GPT","Claude","Anthropic","Gemini","AI","HBM","NVIDIA","TSMC","ASML",
      "quantum","robotics","autonomous"
    ],
    person: [
      "방한","내한","회담","발언","인터뷰","기자회견","취임","사임","임명",
      "visit","speech","interview","press conference","announce","statement",
      "CEO","대통령","총리","장관"
    ],
    disaster: [
      "지진","쓰나미","화재","폭발","사고","추락","침몰","산사태","홍수","태풍",
      "earthquake","tsunami","fire","explosion","crash","flood","typhoon","landslide"
    ],
    regulatory: [
      "금리","FOMC","한은","기준금리","규제","법안","환율","원달러","달러인덱스",
      "물가지수","CPI","PPI","rate","Fed","regulation","bill","policy","inflation"
    ]
  };

  const TIEBREAK_PRIORITY = ['health','geopolitical','tech','disaster','regulatory','person'];

  // ===== Phonological stopwords =====
  const STOPWORDS_MULTI = new Set([
    "오늘","어제","내일","이번","지난","최근","올해","작년","내년",
    "발표","공개","공시","출시","참가","방한","내한","회담","협력",
    "투자","추가","확대","발견","선언","분석","조사","참석","선포",
    "고조","모색","긴장","충돌","급등","급락","출범","선출","관측",
    "주장","강조","예상","계획","추진","체결","협상","검토","검찰",
    "지지","반대","수상","포착","발생",
    "정부","관련","기준","예상","전망","보고","성장","감소","기업과",
    "한국","국내","해외","글로벌",
    "통해","위해","대해","따른","또한","하지만",
    "주식","종목","상장","공급","관심","확정"
  ]);
  const STOPWORDS_SINGLE = new Set([
    "이","그","저","또","다","두","세","네","큰","작",
    "전","후","초","말","신","구","고","더","덜","약",
    "왜","뭐","수","년","월","일","시","분"
  ]);

  // ===== Layer B 카테고리 → 종목명 테마 키워드 =====
  const CATEGORY_THEME_KEYWORDS = {
    health: ["바이오","제약","백신","진단","메디","팜","셀","헬스","한미","녹십자","셀트리온"],
    tech: ["반도체","소프트","테크","솔루션","정보","시스템","전자","디지털","네트워크"],
    geopolitical: ["방산","항공우주","에어로","조선"],
    disaster: ["건설","보험","복구"],
    regulatory: ["증권","금융","은행","보험","캐피탈"],
    person: []
  };

  const SCORE = {
    EXACT: 0.55,
    FIRST_TWO: 0.40,
    FIRST_ONE: 0.30,
    SINGLE_TOKEN_PENALTY: 0.7,
    KEYWORD_SUBSTRING: 0.50,
    THEME_ONLY: 0.40
  };

  function isKoreanChar(c) {
    return c >= '가' && c <= '힣';
  }
  function isKorean(s) {
    return Array.from(s || '').some(isKoreanChar);
  }
  function isAsciiOnly(s) {
    return /^[\x00-\x7F]+$/.test(s);
  }

  // ===== 분류기 (Python classify 그대로) =====
  function classify(text) {
    if (!text) return { category: 'unknown', keywords: [] };
    const textLower = text.toLowerCase();
    const matches = {};
    for (const [cat, kws] of Object.entries(CATEGORY_KEYWORDS)) {
      const hits = [];
      for (const kw of kws) {
        if (isAsciiOnly(kw)) {
          const re = new RegExp('\\b' + kw.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b');
          if (re.test(textLower)) hits.push(kw);
        } else {
          if (text.includes(kw)) hits.push(kw);
        }
      }
      if (hits.length) matches[cat] = hits;
    }
    if (Object.keys(matches).length === 0) return { category: 'unknown', keywords: [] };
    const maxCount = Math.max(...Object.values(matches).map(v => v.length));
    const topCandidates = Object.entries(matches).filter(([_, v]) => v.length === maxCount).map(([k]) => k);
    let chosen = topCandidates[0];
    for (const c of TIEBREAK_PRIORITY) {
      if (topCandidates.includes(c)) { chosen = c; break; }
    }
    const seen = new Set();
    const allKw = [];
    for (const kws of Object.values(matches)) {
      for (const k of kws) {
        if (!seen.has(k)) { seen.add(k); allKw.push(k); }
      }
    }
    return { category: chosen, keywords: allKw };
  }
  function matchesAnyKeyword(text, watchKeywords) {
    if (!text) return [];
    const textLower = text.toLowerCase();
    const hits = [];
    for (const kw of watchKeywords) {
      if (isAsciiOnly(kw)) {
        const re = new RegExp('\\b' + kw.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b');
        if (re.test(textLower)) hits.push(kw);
      } else {
        if (text.includes(kw)) hits.push(kw);
      }
    }
    return hits;
  }

  // ===== KRX Stock DB =====
  class KRXStockDB {
    constructor(stocks) {
      // stocks: Array<[code, name, market, marcap_eok]>
      this.stocks = stocks.map(([c, n, m, k]) => ({ code: c, name: n, market: m, marcapEok: k }));
      this.byFirstSyllable = new Map();
      this.bySubstring = new Map();
      for (const s of this.stocks) {
        if (s.name.length === 0) continue;
        const first = s.name[0];
        if (!this.byFirstSyllable.has(first)) this.byFirstSyllable.set(first, []);
        this.byFirstSyllable.get(first).push(s);
        // bigram 인덱스
        for (let i = 0; i < s.name.length - 1; i++) {
          const bg = s.name.slice(i, i + 2);
          if (!this.bySubstring.has(bg)) this.bySubstring.set(bg, []);
          const list = this.bySubstring.get(bg);
          if (!list.includes(s)) list.push(s);
        }
      }
    }
    static async fromUrl(url) {
      const candidates = ['data/krx_stocks.json', '../data/krx_stocks.json', './data/krx_stocks.json'];
      const tryUrls = url ? [url, ...candidates] : candidates;
      for (const u of tryUrls) {
        try {
          const r = await fetch(u);
          if (!r.ok) continue;
          const data = await r.json();
          return new KRXStockDB(data);
        } catch (_) { /* try next */ }
      }
      throw new Error('krx_stocks.json 로드 실패. URL 시도: ' + tryUrls.join(', '));
    }
    findByFirstSyllable(syl) { return this.byFirstSyllable.get(syl) || []; }
    findBySubstring(substr) {
      if (!substr) return [];
      if (substr.length === 1) {
        return this.stocks.filter(s => s.name.includes(substr));
      }
      const candidates = this.bySubstring.get(substr.slice(0, 2)) || [];
      if (substr.length === 2) return candidates.slice();
      return candidates.filter(s => s.name.includes(substr));
    }
  }

  // ===== Phonological Matcher (Layer A) =====
  function matchPhonological(event, db, opts) {
    const minMarcap = opts.minMarcap || 0;
    const maxMarcap = opts.maxMarcap || 0;  // 0 = no upper limit
    const maxPerToken = opts.maxPerToken || 5;
    const text = event.title || '';
    // 1-5자 한국어 토큰
    const tokens = Array.from(text.matchAll(/[가-힣]{1,5}/g)).map(m => m[0]);
    const seenFirst = new Set();
    const uniqueTokens = [];
    for (const tok of tokens) {
      if (tok.length === 1) {
        if (STOPWORDS_SINGLE.has(tok)) continue;
      } else {
        if (STOPWORDS_MULTI.has(tok)) continue;
      }
      if (seenFirst.has(tok[0])) continue;
      seenFirst.add(tok[0]);
      uniqueTokens.push(tok);
    }
    const candidates = [];
    for (const token of uniqueTokens) {
      const stocks = db.findByFirstSyllable(token[0]);
      const scored = [];
      for (const s of stocks) {
        if (s.marcapEok < minMarcap) continue;
        if (maxMarcap > 0 && s.marcapEok > maxMarcap) continue;
        const sc = scorePhonological(token, s.name);
        if (sc.score === 0) continue;
        let finalScore = sc.score;
        if (token.length === 1) finalScore *= SCORE.SINGLE_TOKEN_PENALTY;
        scored.push({ score: finalScore, kind: sc.kind, stock: s });
      }
      scored.sort((a, b) => (b.score - a.score) || ((b.stock.marcapEok || 0) - (a.stock.marcapEok || 0)));
      let picked = 0;
      for (const e of scored) {
        candidates.push({
          stock_code: e.stock.code,
          stock_name: e.stock.name,
          market: e.stock.market,
          marcap_eok: e.stock.marcapEok,
          trigger_event_id: event.event_id || event.id || '',
          layer: 'phonological',
          score: e.score,
          matched_on: token,
          reason: `트리거 토큰 '${token}'의 첫 음절 '${token[0]}'이 종목명 '${e.stock.name}'의 첫 음절과 일치 (${e.kind})`,
          details: { token, first_syllable: token[0], match_kind: e.kind }
        });
        picked++;
        if (picked >= maxPerToken) break;
      }
    }
    return candidates;
  }
  function scorePhonological(token, stockName) {
    if (!token || !stockName) return { score: 0, kind: 'none' };
    if (token === stockName) return { score: SCORE.EXACT, kind: 'exact' };
    if (token.length >= 2 && stockName.length >= 2 && token[0] === stockName[0] && token[1] === stockName[1]) {
      return { score: SCORE.FIRST_TWO, kind: 'first2' };
    }
    if (token[0] === stockName[0]) return { score: SCORE.FIRST_ONE, kind: 'first1' };
    return { score: 0, kind: 'none' };
  }

  // ===== Semantic Matcher (Layer B) =====
  function matchSemantic(event, db, opts) {
    const minMarcap = opts.minMarcap || 0;
    const maxMarcap = opts.maxMarcap || 0;
    const maxPerKeyword = opts.maxPerKeyword || 8;
    const minKwLength = 2;
    const seenCodes = new Set();
    const candidates = [];
    // 1) 이벤트 키워드 substring (강한 신호)
    const evKeywords = event.keywords || [];
    for (const kw of evKeywords) {
      if (!isKorean(kw) || kw.length < minKwLength) continue;
      const stocks = db.findBySubstring(kw);
      const sorted = stocks.slice().sort((a, b) => (b.marcapEok || 0) - (a.marcapEok || 0));
      let picked = 0;
      for (const s of sorted) {
        if (seenCodes.has(s.code)) continue;
        if (s.marcapEok < minMarcap) continue;
        if (maxMarcap > 0 && s.marcapEok > maxMarcap) continue;
        seenCodes.add(s.code);
        candidates.push({
          stock_code: s.code,
          stock_name: s.name,
          market: s.market,
          marcap_eok: s.marcapEok,
          trigger_event_id: event.event_id || event.id || '',
          layer: 'semantic',
          score: SCORE.KEYWORD_SUBSTRING,
          matched_on: kw,
          reason: `이벤트 키워드 '${kw}'가 종목명 '${s.name}'에 직접 포함됨`,
          details: { match_kind: 'keyword_substring', category: event.category }
        });
        picked++;
        if (picked >= maxPerKeyword) break;
      }
    }
    // 2) 카테고리 → 테마 키워드 (약한 신호)
    const themes = CATEGORY_THEME_KEYWORDS[event.category] || [];
    for (const theme of themes) {
      const stocks = db.findBySubstring(theme);
      const sorted = stocks.slice().sort((a, b) => (b.marcapEok || 0) - (a.marcapEok || 0));
      let picked = 0;
      for (const s of sorted) {
        if (seenCodes.has(s.code)) continue;
        if (s.marcapEok < minMarcap) continue;
        if (maxMarcap > 0 && s.marcapEok > maxMarcap) continue;
        seenCodes.add(s.code);
        candidates.push({
          stock_code: s.code,
          stock_name: s.name,
          market: s.market,
          marcap_eok: s.marcapEok,
          trigger_event_id: event.event_id || event.id || '',
          layer: 'semantic',
          score: SCORE.THEME_ONLY,
          matched_on: theme,
          reason: `이벤트 카테고리 '${event.category}'의 테마 키워드 '${theme}'가 종목명 '${s.name}'에 포함됨`,
          details: { match_kind: 'category_theme', category: event.category }
        });
        picked++;
        if (picked >= maxPerKeyword) break;
      }
    }
    return candidates;
  }

  // ===== 통합 매칭 엔진 =====
  class MatcherEngine {
    constructor() {
      this.db = null;
    }
    async loadKRXDB(url) {
      this.db = await KRXStockDB.fromUrl(url);
      return this.db.stocks.length;
    }
    /** 단일 이벤트의 카테고리/키워드 분류 (events.json에 없으면 보충) */
    enrichEvent(event) {
      if (event.category && event.keywords && event.keywords.length > 0) return event;
      const text = (event.title || '') + ' ' + (event.body || '');
      const cls = classify(text);
      return {
        ...event,
        category: event.category || cls.category,
        keywords: event.keywords && event.keywords.length ? event.keywords : cls.keywords
      };
    }
    /** 키워드 사전 매칭 (트리거 이벤트 필터) */
    filterByKeywords(events, watchKeywords) {
      if (!watchKeywords || watchKeywords.length === 0) return events;
      return events.filter(ev => {
        const text = (ev.title || '') + ' ' + (ev.body || '');
        return matchesAnyKeyword(text, watchKeywords).length > 0;
      });
    }
    /** events → matches.json 형식 결과 */
    match(events, opts) {
      if (!this.db) throw new Error('loadKRXDB() 먼저 호출해야 함');
      opts = opts || {};
      const enrichedEvents = events.map(e => this.enrichEvent(e));
      const perStock = new Map();
      const allCandidates = [];
      for (const ev of enrichedEvents) {
        const cands = [
          ...matchPhonological(ev, this.db, opts),
          ...matchSemantic(ev, this.db, opts)
        ];
        for (const c of cands) {
          c.event_title = ev.title;
          c.event_category = ev.category;
          c.event_url = ev.url;
          allCandidates.push(c);
          if (!perStock.has(c.stock_code)) {
            perStock.set(c.stock_code, {
              stock_code: c.stock_code,
              stock_name: c.stock_name,
              market: c.market,
              marcap_eok: c.marcap_eok,
              total_score: 0,
              max_score: 0,
              match_count: 0,
              layers: new Set(),
              matches: []
            });
          }
          const agg = perStock.get(c.stock_code);
          agg.total_score += c.score;
          if (c.score > agg.max_score) agg.max_score = c.score;
          agg.match_count++;
          agg.layers.add(c.layer);
          agg.matches.push({
            event_title: ev.title,
            event_category: ev.category,
            layer: c.layer,
            score: Math.round(c.score * 1000) / 1000,
            matched_on: c.matched_on
          });
        }
      }
      const topStocks = Array.from(perStock.values()).map(s => ({
        ...s,
        layers: Array.from(s.layers).sort()
      }));
      return {
        generated_at: new Date().toISOString(),
        input_events: '(client-side)',
        event_count: enrichedEvents.length,
        stock_db_count: this.db.stocks.length,
        filter: {
          min_marcap_eok: opts.minMarcap || 0,
          max_marcap_eok: opts.maxMarcap || 0,
          max_per_token: opts.maxPerToken || 5,
          max_per_keyword: opts.maxPerKeyword || 8
        },
        top_stocks: topStocks,
        all_candidates: allCandidates
      };
    }
  }

  // ===== KRX Sector DB (Sprint 2 — 실사업 구분) =====
  // data/krx_sectors.json: [[code, industry, products], ...]
  // 사명 매칭(예: 사피엔반도체="반도체")이 종목의 실제 Industry/Products와 일치하는지 cross-check
  class KRXSectorDB {
    constructor(rows) {
      // rows: [[code, industry, products], ...]
      this.byCode = new Map();
      for (const [c, ind, prod] of rows) {
        this.byCode.set(c, { industry: ind || '', products: prod || '' });
      }
    }
    static async fromUrl(url) {
      const candidates = ['data/krx_sectors.json', '../data/krx_sectors.json', './data/krx_sectors.json'];
      const tryUrls = url ? [url, ...candidates] : candidates;
      for (const u of tryUrls) {
        try {
          const r = await fetch(u);
          if (!r.ok) continue;
          const data = await r.json();
          return new KRXSectorDB(data);
        } catch (_) {}
      }
      return null;  // fallback — null 반환 (cross-check 단순 skip)
    }
    /** 키워드가 종목의 Industry+Products 텍스트에 포함되는지 */
    isKeywordInBusiness(stockCode, keyword) {
      const s = this.byCode.get(stockCode);
      if (!s) return null;  // 미등록 종목
      if (!keyword) return false;
      const blob = (s.industry + ' ' + s.products).toLowerCase();
      return blob.includes(keyword.toLowerCase());
    }
    getBusinessText(stockCode) {
      const s = this.byCode.get(stockCode);
      if (!s) return null;
      return { industry: s.industry, products: s.products };
    }
  }

  /** 단일 매칭의 진정성 분류 */
  function classifyMatchAuthenticity(match, stockCode, stockName, sectorDB) {
    // Layer A (음운)은 사명 first-syllable 매칭 — 의미 매칭과 다른 본질이라 'phonological' 그대로
    if (match.layer === 'phonological') return 'phonological';
    if (!sectorDB) return 'unknown';
    const matchedOn = match.matched_on || '';
    // 사명에 포함됐는지
    const inName = stockName.includes(matchedOn);
    // Industry/Products에 포함됐는지
    const inBusiness = sectorDB.isKeywordInBusiness(stockCode, matchedOn);
    if (inBusiness === null) return 'unknown';  // 섹터 정보 없음
    if (inBusiness) return 'genuine';            // 실제 사업과 일치
    if (inName) return 'name_only';              // 사명에만 있음 → 부작용
    return 'standard';                            // 기타 (있을 법한 카테고리 테마)
  }

  // ===== Export =====
  global.DantaLink = global.DantaLink || {};
  global.DantaLink.MatcherEngine = MatcherEngine;
  global.DantaLink.KRXStockDB = KRXStockDB;
  global.DantaLink.KRXSectorDB = KRXSectorDB;
  global.DantaLink.classifyMatchAuthenticity = classifyMatchAuthenticity;
  global.DantaLink.classify = classify;
  global.DantaLink.matchesAnyKeyword = matchesAnyKeyword;
  global.DantaLink.CATEGORY_KEYWORDS = CATEGORY_KEYWORDS;
})(typeof window !== 'undefined' ? window : globalThis);
