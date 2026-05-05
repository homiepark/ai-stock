# 다음에 해야 할 것 — 처음부터 운영까지 체크리스트

> 시스템은 만들어져 있고 테스트도 통과 상태. 이제 **실제로 본인 환경에서 돌리는 순서**입니다.
> 30분~1시간이면 끝.

---

## ✅ Step 1: 첫 리포트 한 번 돌려보기 (10분)

### 1-1. Anthropic API 키 발급
1. https://console.anthropic.com 접속 → 계정 생성
2. Settings → API Keys → "Create Key"
3. 키 복사 (sk-ant-... 으로 시작)
4. 결제카드 등록 + **$5~10 충전** (한 달 운영 비용 추정)

> 💰 **비용 가늠**: 매일 50종목 중 Top 5에만 LLM 서술 생성 → 하루 약 $0.10~0.30 → 한 달 약 $3~10. Prompt caching 켜져 있어 같은 종목 반복 분석 시 90% 할인.

### 1-2. 환경 설정
```bash
cd /home/user/ai-stock
cp .env.example .env
# .env 파일 열어서 ANTHROPIC_API_KEY=sk-ant-... 입력
uv sync
```

### 1-3. 첫 리포트 실행
```bash
uv run ai-stock daily
```

리포트 위치: `reports/daily/2026-XX-XX.md`. 열어서 확인.

### 1-4. 잘 됐는지 확인
- [ ] 매크로 스냅샷 표에 숫자가 들어감 (- 만 있으면 yfinance가 막힌 것)
- [ ] 종합 판정 매트릭스에 50개 가까운 종목이 있음
- [ ] Top 5 종목의 LLM 서술이 "API 키 미설정"이 **아닌** 진짜 분석 텍스트
- [ ] 라벨 (🟢🟡⚪🟠🔴) 이모지가 보임

3개 이상 ❌면 → `docs/AUTOMATION.md` "자동화 안 도는 흔한 이유" 섹션 참조.

---

## ✅ Step 2: 워치리스트 본인 취향대로 조정 (선택)

### 50종목 그대로 써도 OK
선별 기준은 `docs/UNIVERSE_RATIONALE.md`에 정리.

### 종목 추가/제거하고 싶다면
`config/universe.yaml` 직접 편집:

```yaml
themes:
  vertical_ai:
    stocks:
      # 한 줄 추가
      - { ticker: ADBE, country: US, tier: supporting, name: "Adobe", note: "AI 위협 회복 트래킹" }
```

저장 후:
```bash
uv run ai-stock universe   # 변경 확인
uv run ai-stock daily      # 다음 리포트부터 반영
```

### 일회성 종목이 궁금하다면 (워치리스트 변경 X)
```bash
uv run ai-stock analyze AAPL              # 미국 주식
uv run ai-stock analyze 005930            # 한국 주식 6자리 코드
uv run ai-stock analyze NVDA --name 엔비디아
```

`reports/adhoc/<TICKER>-YYYY-MM-DD.md`에 저장. 분석 결과 마음에 들면 → `config/universe.yaml`에 추가해 매일 추적.

---

## ✅ Step 3: 자동화 걸기 (10분)

`docs/AUTOMATION.md` 참조. 방법 3개 중 **GitHub Actions 추천** (컴퓨터 안 켜도 됨).

### 빠른 GitHub Actions 설정
1. 깃허브 저장소 → Settings → Secrets → New secret
   - Name: `ANTHROPIC_API_KEY`, Value: `sk-ant-...`
2. `.github/workflows/daily-report.yml` 파일은 **이미 저장소에 들어있음**.
3. Actions 탭 → "Daily AI Stock Report" → "Run workflow"로 즉시 한 번 테스트.
4. 성공하면 매주 화~토 한국시간 06:30에 자동 실행.

설정 끝. 매일 아침 일어나서 깃허브 앱 → reports/daily/ 최신 리포트 확인.

---

## ✅ Step 4: 며칠 운영해보고 튜닝 (1주일)

### 1~3일차
- 매일 아침 리포트 확인.
- LLM 라벨이 본인 직관과 어긋나면 → 본인이 옳은지 LLM이 옳은지 비교.
- 점수가 매번 비슷하다면 → 가중치 조정 필요 (`config/settings.yaml`).

### 4~7일차
- 라벨 변경 트래킹 (리포트 § 6 "포지션 리뷰") 보면서 시스템이 시그널 감지하는지 검증.
- 실제 매매 의사결정에 참고. **이 시스템은 보조 도구지 의사결정 자동화가 아님**.

### 한 달 후
- 어떤 신호가 적중률 높은지 감 잡힘 → `config/settings.yaml`의 가중치 미세 조정.
- 무료 데이터 한계 느껴지면 → Polygon 등 유료 API 도입 고려.
- 대시보드(Phase 2) 필요 시점 판단.

---

## 📚 모르는 게 나오면

| 질문 | 참조 |
|---|---|
| RSI? EV/Sales? HBM? CoWoS? 같은 단어들 | **`docs/GLOSSARY.md`** — 한 줄 정의 + 일상어 비유로 모두 풀어놨음 |
| 왜 이 50종목인지, 빠진 종목은 왜 빠졌는지 | **`docs/UNIVERSE_RATIONALE.md`** |
| 매일 자동 실행 설정 | **`docs/AUTOMATION.md`** |
| 워치리스트 외 종목 보고 싶을 때 | `ai-stock analyze <TICKER>` |
| 코드가 뭘 하는지 | `README.md` 의 아키텍처 섹션 |

---

## 🚦 운영 원칙 (꼭 읽기)

1. **이 시스템은 의사결정 보조다, 자동매매가 아니다**.
   라벨 STRONG_BUY가 떠도 본인 판단으로 사세요. 시스템은 정보를 정리할 뿐.

2. **매크로(금리, 환율) 동향은 항상 본다**.
   아무리 좋은 종목이라도 매크로 역풍이면 짧게 갈 수 있음.

3. **분할매수 가이드를 무시하지 말 것**.
   LLM이 "1차 X에서 50%, 2차 Y에서 50%"라고 하면 Y에서 더 떨어졌을 때 추가 매수할 자금을 남겨두라는 의미.

4. **라벨이 STRONG_BUY → ACCUMULATE → HOLD로 내려가는 흐름이 더 중요**.
   1회 라벨보다 추세가 정보량 많음.

5. **리스크 섹션 꼭 읽기**.
   기회만 보면 망함.

6. **6주마다 한 번씩 점검**.
   - 무료 데이터로 충분한가?
   - 라벨 적중률 어땠나?
   - 워치리스트 손볼 곳 있나?

---

다음 액션이 명확하지 않으면 **Step 1부터** 차근히 진행하세요.
