# ai-stock

AI 투자 일일 분석 시스템 — "**철도 = AI**" 사이클 가설을 추적하기 위한 워치리스트 + 매수 판정 엔진.

매일 4대 자산 계층(전력·반도체·하이퍼스케일러·운영자) + Embodied AI 약 50종목(미국 70% / 한국 30%)에 대해:

- 단기(1~12주) / 중기(3~12개월) / 장기(1~5년) 정량 점수
- 5단계 라벨: 🟢 STRONG_BUY · 🟡 ACCUMULATE · ⚪ HOLD · 🟠 TRIM · 🔴 AVOID
- Claude API가 작성한 진입 가이드 + 리스크 + 다음 트리거 이벤트
- 테마 모멘텀 랭킹 + 시총 대장 / 모멘텀 대장 식별
- 뉴스 다이제스트 (워치리스트 종목 관련만 필터링)
- 어제 대비 라벨 변경 추적

리포트는 `reports/daily/YYYY-MM-DD.md`에 저장 → git에 커밋 → 깃허브/노션/모바일에서 어디서든 열람.

## 📖 가장 먼저 볼 문서

| 질문 | 문서 |
|---|---|
| **VSCode·터미널 처음이라면?** | [docs/SETUP.md](docs/SETUP.md) — 0부터 시작하는 환경 설정 (Mac / Win) |
| **본인 사이트 만들고 싶다면?** | [docs/SITE_SETUP.md](docs/SITE_SETUP.md) — GitHub Pages + 자동 배포 |
| **환경 설정 끝났다면 뭐부터?** | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) — 단계별 운영 체크리스트 |
| **모르는 용어가 있다** | [docs/GLOSSARY.md](docs/GLOSSARY.md) — RSI, HBM, CoWoS 등 모든 용어 한 줄 설명 |
| **왜 이 50종목인가?** | [docs/UNIVERSE_RATIONALE.md](docs/UNIVERSE_RATIONALE.md) — 종목별 선별 이유 |
| **🪙 코인 워치리스트 기준은?** | [docs/COIN_UNIVERSE_RATIONALE.md](docs/COIN_UNIVERSE_RATIONALE.md) — 6대 매집 기준 + Messari Theses 2026 반영 |
| **🔥 트위터 인플루언서 트래킹은?** | [docs/SOCIAL_TRACKING.md](docs/SOCIAL_TRACKING.md) — X API 가격·대안·단계별 업그레이드 |
| **매일 자동 실행은?** | [docs/AUTOMATION.md](docs/AUTOMATION.md) — GitHub Actions / cron / launchd |

## 빠른 시작

```bash
# 1) 의존성 설치 (uv 권장)
uv sync

# 2) API 키 설정 (Claude 서술 분석에 필요)
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력

# 3) 워치리스트 확인
uv run ai-stock universe

# 4) 일일 리포트 생성
uv run ai-stock daily
# → reports/daily/2026-05-05.md

# 5) 워치리스트 외 종목 임시 분석
uv run ai-stock analyze NVDA       # 미국 주식
uv run ai-stock analyze 005930     # 한국 주식 (6자리 코드)
# → reports/adhoc/<TICKER>-2026-05-05.md
```

`ANTHROPIC_API_KEY`가 없으면 Claude 서술은 생략되고 정량 점수만 출력됩니다.

## 자동화 (cron)

미국장 마감 후 한국시간 06:30에 자동 실행:

```cron
30 6 * * 2-6 cd /path/to/ai-stock && uv run ai-stock daily \
  && git -C . add reports && git -C . commit -m "daily $(date +%F)" && git push
```

## 샘플 리포트

`reports/samples/`에 정량 점수 + 합성 데이터로 만든 미리보기 리포트가 있습니다.
실제 시장 데이터 대신 결정론적 합성 가격을 사용하므로 출력 형식 확인용입니다.

```bash
uv run python scripts/generate_sample_report.py
```

## 아키텍처

```
src/ai_stock/
├── data/         # yfinance, pykrx, FRED, RSS 어댑터 + 디스크 캐시
├── signals/      # 단기/중기/장기 정량 신호 + 테마 모멘텀
├── judge/        # 정량 점수 합산 + Claude API로 5단계 라벨링
├── report/       # Jinja2 템플릿으로 일일 Markdown 리포트 생성
└── cli.py        # `ai-stock daily`, `ai-stock universe`
```

설계 원칙:

1. **데이터 · 신호 · 판정 · 출력 4단 분리** — 한 단계 교체가 다른 단을 깨지 않음.
2. **결정론적 부분(점수)과 LLM 부분(서술)의 명확한 경계** — 점수는 코드, 글은 Claude.
3. **모든 리포트는 git 커밋** — "내가 3주 전에 뭐라 생각했지?" 시계열 추적.
4. **Prompt caching 적극 활용** — 회사별 고정 thesis는 캐시, 일일 갱신분만 변동.
5. **YAGNI** — Phase 1은 Markdown만. 대시보드는 명확한 필요 발생 후.

## 워치리스트 변경

`config/universe.yaml` 편집 — 테마, 종목, 투자 논거(thesis) 모두 여기서.

```yaml
themes:
  semiconductors:
    name: "반도체·HBM·패키징"
    thesis: "..."
    stocks:
      - { ticker: NVDA, country: US, tier: leader, name: "NVIDIA", note: "..." }
```

## 테스트

```bash
uv run pytest -q
```

20개 단위/통합 테스트 — 가격 신호, 점수 계산, 리포트 렌더링까지 네트워크 없이 검증.

## 데이터 소스 (전부 무료)

- **미국 가격/펀더멘털**: yfinance
- **한국 가격**: pykrx (KRX)
- **매크로**: yfinance 인덱스 프록시 (FRED 없이도 작동)
- **뉴스**: RSS (Reuters, Bloomberg, CNBC, TechCrunch, 한국경제, 전자신문)
- **LLM**: Anthropic Claude API (`claude-opus-4-7`)

운영 중 한계가 명확해지면 (실시간 시세, 옵션, 정제된 뉴스) Polygon/FinancialDatasets 등 유료 API를 핀포인트로 추가.

## 다음 단계 (Phase 2 후보)

- Streamlit 대시보드 — 동일 데이터/신호 위에 인터랙티브 시각화
- 종목 1개 딥다이브 리포트 (`ai-stock deepdive NVDA`)
- 슬랙/디스코드 알림 (라벨 변경 시)
- 백테스트 — 라벨 변경 시점 대비 수익률 검증
