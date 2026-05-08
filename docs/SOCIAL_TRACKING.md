# 트위터·소셜 인플루언서 트래킹 — 가능한 것과 한계

> **요약**: 2024년 이후 X(트위터)는 무료 실시간 트래킹이 사실상 불가능. 본 시스템은 ApeWisdom 집계 데이터(무료, 신뢰도 높음)로 80% 커버하고, 큐레이션된 인플루언서 명단으로 컨텍스트 제공. 진짜 실시간 개별 트윗 추적은 X API 유료 ($200~$5,000/월) 필요.

---

## 🎯 현재 시스템이 하는 것 (무료)

### 1. ApeWisdom 집계 (메인)
- **출처**: https://apewisdom.io
- **방식**: Reddit r/CryptoCurrency, Twitter, Discord에서 코인 언급량 집계
- **신뢰도**: ⭐⭐⭐⭐ (정상 작동, 1시간 이내 업데이트)
- **이 시스템에서**: 코인별 24시간 멘션 변화율 → 'RISING 🔥' 신호
- **장점**: 인플루언서·일반 유저 구분 없이 **전체 사회적 관심도** 캐치
- **단점**: 어떤 인플루언서가 말했는지는 모름, 1시간 지연

### 2. 큐레이션된 인플루언서 명단 (참고용)
30명을 5개 카테고리로 분류해서 워치리스트로 제공:

| 카테고리 | 대표 계정 | 영향력 |
|---|---|---|
| **밈코인 알파** | Ansem (@blknoiz06), Murad (@MustStopMurad) | ⭐⭐⭐⭐⭐ |
| **베테랑 트레이더** | Cobie (@cobie), Pentoshi (@Pentosh1), Hsaka | ⭐⭐⭐⭐⭐ |
| **데이터 분석가** | DefiIgnas, tayvano_, Cryptopathic | ⭐⭐⭐⭐ |
| **창립자** | Vitalik, Mert (Solana), Anatoly | ⭐⭐⭐⭐⭐ |
| **내러티브** | DonAlt, Will Clemente, Wale Swoosh | ⭐⭐⭐⭐ |

전체 명단은 `config/influencers.yaml`에서 편집 가능. 사이트의 "🔥 트위터 펄스" 섹션에서 명단 펼치고 클릭 → 본인 X 앱에서 직접 확인.

---

## ⭐ 추천: Sorsa API (전 TweetScout) — X API 대비 50배 저렴

**가장 가성비 좋은 옵션.** 크립토 트위터에 특화돼 있고, 공식 X API보다 50배 저렴 + 20배 높은 rate limit. 이 시스템은 **API 키만 넣으면 즉시 동작**하도록 통합 완료됨.

### Sorsa 가격·기능 (2026 기준)

| 플랜 | 월 비용 | 월 요청 한도 | 30명 인플루언서 폴링 |
|---|---:|---:|---|
| **Starter** | **$49** | ~10,000 | 3시간 간격 OK |
| **Pro** | **$199** | ~100,000 | 1시간 간격 OK + 추가 검색 여유 |

**X API Basic($200)과 Sorsa Pro($199) 비교**:
- 가격 비슷 ($200 vs $199)
- Sorsa는 **rate limit 10배 높음** (10K → 100K)
- Sorsa는 **크립토 특화 점수**(Sorsa Score) + **봇 탐지** 추가
- Sorsa는 즉시 셋업 (X API는 승인 1~3일)

→ **개인 투자자에겐 Sorsa Pro가 X API Basic보다 명백히 우위**.

### Sorsa 활성화 방법

1. https://sorsa.io 가입 (또는 https://app.tweetscout.io)
2. API 키 발급 → `.env`에 추가:
   ```
   SORSA_API_KEY=your_key_here
   ```
3. `config/influencers.yaml`에서 `sorsa.enabled: true`로 변경
4. `uv run ai-stock daily` 실행 → 코인 페이지에 인플루언서 실제 트윗 + Sorsa Score 자동 노출

### 작동 방식 (시스템 내부)

- **`min_score: 50`** 미만 계정은 폴링 전 스킵 → 봇·돈주고 산 팔로워 계정 자동 제외
- 폴링 우선순위: weight 높은 인플루언서부터 (가중치 10인 Ansem이 가중치 5인 사람보다 먼저)
- 트윗은 **weight × 좋아요·리트윗 수**로 정렬해서 진짜 영향력 큰 트윗 상단
- 18시간 캐시로 같은 데이터 중복 호출 방지

---

## 💰 X (Twitter) 공식 API 티어별 트래킹 능력

**X API는 2023년 4월 무료 티어 제거 이후 완전 유료화**됨. 2026년 5월 기준 가격:

### Free (무료)
- **트래킹**: ❌ 거의 불가
- 본인 계정 글쓰기만 가능 (월 1,500 트윗)
- 다른 사용자 트윗 읽기 사실상 불가

### Basic ($200/월)
- **트래킹**: ⚠️ 빠듯함, 폴링 간격 4~6시간
- 월 10,000 트윗 읽기
- 최근 7일 검색 가능
- 필터 스트림 (제한적, 50개 규칙)
- **30명 인플루언서를 4시간마다 폴링하면 한도 안에 들어감**
- 30명 × 6회/일 × 30일 = 5,400 reads/월 → OK
- **이게 가성비 최고. 진짜 알파 노릴 때 추천.**

### Pro ($5,000/월)
- **트래킹**: ✅ 실시간 가능
- 월 100만 트윗 읽기 (사실상 무제한)
- 풀 아카이브 검색 (전체 역사)
- 고대역 필터 스트림
- **분 단위 폴링 + 키워드 실시간 알림 가능**
- 개인 투자자에게는 오버스펙

### Enterprise (협의)
- **트래킹**: ✅ 풀 firehose
- 가격: 수만 달러/월
- 헤지펀드·기관 투자자용

---

## 📊 가성비 대안 (X API 외)

### LunarCrush ($24~99/월)
- 인플루언서 가중 감성 점수
- Galaxy Score (소셜 + 가격 종합)
- 개별 트윗 X, **집계 시그널 O**
- API 잘 정리됨
- **추천**: Stage 2 옵션 ($24 기본 플랜)

### Apify Twitter Scraper ($30~100/월)
- 헤드리스 브라우저로 X 스크래핑
- 가격 변동 큼, 안정성 중간
- ToS 회색 영역 (하지만 단속은 미미)
- 30명 트윗 매시간 폴링: ~$50/월

### TweetScout API (무료~$50)
- 크립토 특화 트위터 분석
- KOL 점수, 가짜 팔로워 탐지
- 무료 티어로도 어느 정도 가능

### Kaito.ai Yaps (무료 대시보드)
- AI가 종합한 크립토 트위터 트렌드
- 대시보드는 무료
- API는 협의 필요

### Cookie3 / Cookie DAO
- 크립토 트위터 reputation tracking
- 주로 프로젝트 평가용
- API 접근 까다로움

---

## 🚦 단계별 업그레이드 경로

### Stage 1: 지금 (무료) ← **현재 상태**
- ApeWisdom 집계 + 큐레이션 명단
- **커버리지 ~80%**: 어느 코인이 핫한지 1시간 이내 캐치, 누가 말했는지는 직접 확인 필요

### Stage 2: $49/월 — **Sorsa Starter (추천)** ⭐
- 30명 인플루언서 3시간마다 폴링 + Sorsa Score(봇 탐지)
- 코드는 이미 구현됨 — `SORSA_API_KEY` 넣고 `sorsa.enabled: true`만 설정
- **커버리지 ~85%**: 진짜 인플루언서 트윗을 사이트에서 직접 확인 가능

### Stage 3: $199/월 — Sorsa Pro
- 30명 인플루언서 1시간마다 폴링 + 키워드 검색 여유
- **커버리지 ~95%**: 거의 실시간, 개별 트윗 추적
- X API Basic($200) 대비 rate limit 10배

### Stage 4: $5,000/월 — X API Pro
- 분 단위 추적, 풀 아카이브
- **커버리지 ~99%**: 헤지펀드 수준
- 개인 투자자에겐 오버스펙

### 권장 진행
- 처음 1~2개월: **Stage 1**로 충분히 가치 검증
- 시스템에 익숙해지면: **Stage 2 (Sorsa Starter $49/월)** 추가 — 가성비 최고
- 진짜 알파 노릴 때만: **Stage 3 (Sorsa Pro $199/월)**

### Sorsa보다 LunarCrush가 나은 경우
- 개별 트윗보다 **집계 감성·소셜 점수** 중심 분석을 원할 때
- $24/월로 더 저렴
- 둘 다 사용하는 것도 옵션 (각자 다른 신호)

---

## 🔧 Sorsa 활성화 방법 (Stage 2 / 3)

### 1. API 키 발급
- https://sorsa.io 또는 https://app.tweetscout.io 접속
- 가입 → Developer 섹션 → API key 생성
- Starter $49/월 또는 Pro $199/월 결제

### 2. `.env` 파일에 키 추가
```
SORSA_API_KEY=ts_xxxxxxxxxxxx
```

### 3. `config/influencers.yaml` 활성화
```yaml
sorsa:
  enabled: true
  poll_interval_minutes: 60   # Pro는 60분, Starter는 180분 권장
  tweets_per_influencer: 5
  min_score: 50               # 봇·저신뢰 계정 자동 제외 (Starter는 60+ 권장)
```

### 4. 즉시 동작
```powershell
uv run ai-stock daily
start site\coin.html
```

코인 페이지의 "🔥 트위터 펄스" 섹션에 다음이 자동 추가됨:
- 인플루언서 실제 최근 트윗 (최대 12건)
- 각 트윗의 ❤ 좋아요·🔁 리트윗 수
- Sorsa Score (1~100, 크립토 신뢰도)
- 트윗 클릭 시 X 원본 이동

### 비용 절감 팁
- `poll_interval_minutes`를 `1440`(하루 1회)로 두면 한 달 ~900 calls만 사용 → Starter 한도의 9% 사용으로 적정
- `min_score: 70`으로 올리면 정말 검증된 인플루언서만 노출 → 노이즈 감소
- 워치리스트 인플루언서 30명 → 10명으로 줄이면 비용도 1/3

---

## 🔧 X API Pro 통합 (Stage 4)

X API Pro는 별도 코드가 필요. Sorsa와 다른 인증 + 다른 endpoint shape. 현재 시스템은 placeholder만 있음:

```yaml
x_api:
  enabled: false  # 활성화하려면 src/ai_stock/data/social.py에 fetch_xapi_pulse 추가 필요
```

대부분의 개인 투자자는 **Sorsa Pro로 충분**. X API Pro는 헤지펀드급 사용처가 아니면 오버스펙.

---

## ❓ 자주 묻는 질문

### Q. Nitter 쓰면 무료인 거 아닌가?
A. 2024년 X가 본격 차단 시작. 2026년 현재 대부분의 공용 Nitter 인스턴스가 죽었거나 빈 응답을 줌. 셀프호스팅도 인증 토큰 필요해서 사실상 무용지물.

### Q. RSSHub는?
A. 공용 인스턴스(rsshub.app)는 rate limit 매우 심함. 셀프호스팅하면 동작하지만 X 측이 IP 차단 자주 함. 안정적이지 않음.

### Q. ApeWisdom 데이터가 1시간 지연되면 늦은 거 아닌가?
A. **일반적인 매매에는 충분**. 진짜 1초 단위 알파(MEV 같은)가 필요한 게 아니면 1시간 지연으로도 큰 트렌드의 90%는 캐치 가능. 밈코인 슈퍼사이클의 경우 보통 며칠~몇 주 단위로 가니 1시간은 의미 있는 지연 아님.

### Q. 인플루언서 명단을 본인 입맛대로 바꾸고 싶다
A. `config/influencers.yaml` 편집 후 `uv run ai-stock daily` 한 번 돌리면 다음 리포트부터 반영. weight (1~10) 도 조정 가능 — 본인이 신뢰하는 사람에게 가중치 높게.

---

## 📌 결론

**개인 투자자 입장에서 가장 합리적**:

1. **Stage 1 (무료) 1개월 운영** → 시스템 익숙해지기
2. ApeWisdom의 RISING 신호 + 본인 직접 X 명단 클릭 확인 = 70% 시간 절약
3. 진짜 부족하다 싶으면 **Stage 2 ($24/월) 추가**
4. 큰 베팅 자주 하는 수준이면 **Stage 3 ($200/월) 고려**

**메모**: 인플루언서 트래킹의 가장 큰 함정은 **"확증 편향"**이다. 본인이 이미 믿는 사람의 의견만 가중치 높게 보면 객관성 잃음. ApeWisdom 같은 집계 데이터는 그 함정에서 자유로움.
