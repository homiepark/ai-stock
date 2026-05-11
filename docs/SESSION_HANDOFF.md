# 세션 핸드오프 — 2026-05-11

## 📦 푸시 대기 중인 커밋 2개

이전 세션에서 작업 완료·로컬 커밋 완료·검증 완료된 변경사항이 샌드박스 git 프록시 장애로 푸시 못 됨. 다음 세션 첫 작업으로 푸시.

```
[로컬 main에 있지만 origin에 없음]
7f624b2 Overheat detection + leveraged ETFs + beginner UI + coin fix
cca5e6f UI polish: hero stats + score heatmap + movers + better cards

[이미 origin에 있음]
c6625ec daily report 2026-05-11
```

## ✅ 검증 상태

- Python: **40/40 테스트 통과** (pytest)
- Next.js: **80개 페이지 빌드 성공** (npx next build)
- TypeScript: **무에러** (tsc --noEmit)

## 🎯 새로운 기능 (커밋 내용)

### 1. 과열 감지 시스템
- `src/ai_stock/signals/overheat.py` — 0~100 점수, 4단계 라벨
- `web/components/overheat-badge.tsx` — UI 배지
- `web/components/overheat-badge.tsx` `BuyTimingGuide` — "지금 사도 되나" 명확한 권고

### 2. 레버리지 ETF 11종목
- 미국: TQQQ, SOXL, NVDL, NVDU, TSLL, BITX, ETHU, SQQQ
- 한국: KODEX 레버리지 (122630), KODEX 200선물인버스2X (252670), KODEX 코스닥150레버리지 (233740)
- `config/universe.yaml`에 `leveraged` 테마 추가

### 3. 코인 데이터 안 뜨던 문제 — 근본 원인 수정
**원인 1**: CoinGecko ID 오류 2개
- `fetch-ai` → `artificial-superintelligence-alliance` (ASI 합병 후 슬러그 변경)
- `io` → `io-net`

**원인 2**: CLI가 코인 파이프라인 예외를 조용히 삼킴 — 이제 traceback 출력

**원인 3**: 한 코인 실패시 전체 파이프라인 죽음 — 이제 per-coin try/except로 격리

### 4. 초보자 UX 대폭 개선
- `web/components/glossary.tsx` `Term` 컴포넌트 — 용어 위 마우스 오버시 한 줄 설명 툴팁
- `web/components/beginner-guide.tsx` `BeginnerGuide` — 홈 페이지 상단 접힌 패널, 5단계 라벨/과열도/분할매수/레버리지/텐베거 설명
- 디테일 페이지에 "🎯 지금 사도 되나?" 가이드 박스

### 5. 문서 업데이트
- `docs/GLOSSARY.md` — 과열도·분할매수·레버리지 ETF 정의 추가
- `docs/UNIVERSE_RATIONALE.md` — 레버리지 테마 11종목 상세 설명
- `docs/OVERHEAT_GUIDE.md` (신규) — 라벨×과열도 매트릭스 매수 결정표

## 🚀 다음 세션에서 할 작업

### 1. 푸시 (가장 먼저)
```bash
git push
```

성공하면 Vercel이 자동으로:
- 코인 ID 수정 적용 → 다음 GitHub Actions 실행 때 코인 데이터 살아남
- 새 UI 컴포넌트 반영 → 5~10분 후 배포된 사이트에 보임

### 2. GitHub Actions 수동 실행 (코인 데이터 즉시 받기)
1. https://github.com/homiepark/ai-stock/actions/workflows/daily-report.yml
2. Run workflow 클릭
3. 3~5분 후 완료되면 web/data/coin/2026-MM-DD.json 생성
4. Vercel 재배포 자동 트리거

### 3. 사이트 검증
- https://ai-stock-{username}.vercel.app/ 새 UI 확인
  - "초보자 가이드" 접힘 패널 보이는지
  - "STRONG BUY" 종목 디테일 페이지에 "🎯 지금 사도 되나?" 박스 보이는지
  - 종합 매트릭스에 과열도 컬럼 보이는지
  - 매트릭스에 "레버리지 ETF" 테마 필터 보이는지
- https://ai-stock-{username}.vercel.app/coins 에서 코인 데이터 보이는지
- 용어(RSI, MA50 등)에 마우스 오버 시 툴팁 뜨는지

## 🆘 트러블슈팅

### 푸시도 실패하면?
새 세션 한 번 더 시작. 보통 새 샌드박스는 다른 IP·프록시라 성공.

### 코인 데이터 여전히 비어있으면?
1. `uv run ai-stock daily --no-stocks --no-site` 수동 실행해서 에러 확인
2. 새 traceback이 보이면 그 메시지 알려주기

### Vercel 빌드 실패하면?
1. Vercel 대시보드 → Deployments → 실패한 빌드 → Logs
2. 보통 `npm install` 또는 type error
3. 로그 첫 5줄 알려주기
