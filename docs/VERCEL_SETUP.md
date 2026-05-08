# Vercel 배포 — Next.js 인터랙티브 대시보드

> 본 가이드는 새로 만든 **Next.js 대시보드(`web/`)**를 Vercel에 배포하는 절차.
> 기존 GitHub Pages 정적 사이트(`site/`)는 그대로 두고 병행 운영하다가, Vercel이 안정되면 GitHub Pages를 끄면 됩니다.

---

## 🎯 아키텍처 개요

```
┌─────────────────────────────────────────────┐
│  GitHub Actions (매주 화~토 06:30 KST)      │
│  1. uv run ai-stock daily                   │
│     → reports/daily/*.md (Markdown)         │
│     → site/*.html        (정적 HTML, 백업)  │
│     → web/data/*.json    (Next.js 입력)     │
│  2. git commit + push (web/data/ 강제 추가) │
└─────────────────────────────────────────────┘
                    │
                    │ push to main
                    ▼
┌─────────────────────────────────────────────┐
│  Vercel (자동 감지)                         │
│  1. web/ 디렉토리에서 next build            │
│  2. JSON 읽어 ~80개 페이지 정적 생성        │
│  3. CDN 배포                                │
│  → https://ai-stock-username.vercel.app     │
└─────────────────────────────────────────────┘
```

**핵심**: Python은 분석·스코어링, Next.js는 표현. JSON이 그 사이의 계약(contract).

---

## 🚀 Vercel 배포 (5분)

### Step 1. Vercel에 저장소 임포트

1. https://vercel.com 로그인
2. **Add New** → **Project**
3. GitHub 저장소 목록에서 `homiepark/ai-stock` 선택 → **Import**

### Step 2. 프로젝트 설정 ⚠️ 중요

기본 셋업 화면에서:

| 필드 | 값 |
|---|---|
| **Framework Preset** | `Next.js` (자동 감지됨) |
| **Root Directory** | **`web`** ⚠️ |
| **Build Command** | `next build` (기본값 그대로) |
| **Output Directory** | `.next` (기본값 그대로) |
| **Install Command** | `npm install` (기본값 그대로) |
| **Node.js Version** | `20.x` 또는 `22.x` |

**⚠️ Root Directory를 `web`으로 설정**하지 않으면 빌드 실패합니다 (저장소 루트에 package.json이 없음).

### Step 3. 환경변수 (Optional)

Next.js 자체는 환경변수 필요 없음 (정적 사이트). 단, **Vercel이 빌드 중 Python을 돌리지는 않음** — JSON은 GitHub Actions가 미리 커밋한 것을 사용.

만약 Vercel 빌드 단계에서 Python 데이터 새로 생성하고 싶다면 (선택):

| 환경변수 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | sk-ant-... |
| `SORSA_API_KEY` | ts_... (선택) |

→ 그리고 `web/vercel.json`의 buildCommand를 수정해서 Python 호출. **하지만 권장하지 않음** — 빌드 시간·복잡도 ↑, GitHub Actions 분리가 더 깔끔.

### Step 4. Deploy 버튼 클릭

1~2분 후 빌드 완료 → URL 발급:
- 기본: `ai-stock-{username}.vercel.app`
- 또는 커스텀 도메인 연결

### Step 5. 자동 배포 확인

이후 main 브랜치에 push가 들어오면 Vercel이 자동 재빌드. GitHub Actions가 매일 새벽 JSON을 커밋 → Vercel이 자동 감지 → 사이트 갱신.

---

## 🔑 GitHub Actions가 JSON을 푸시하도록 설정

이미 워크플로(`/.github/workflows/daily-report.yml`)에 다음 단계 포함됨:

```yaml
- name: Commit reports + JSON data
  run: |
    git add reports/
    git add -f web/data/        # ← gitignore 무시하고 강제 추가
    git commit -m "daily report $(date +%F)"
    git push
```

추가 조치 불필요. **Vercel이 push 감지해서 자동 배포**.

### 더 정밀한 제어 (선택): Deploy Hook

Push마다 자동 재배포되는 게 부담스러우면 Deploy Hook 사용:

1. Vercel 프로젝트 → Settings → Git → **Deploy Hooks**
2. Hook 이름 "daily-data-update", branch "main" → Create
3. URL 복사 (`https://api.vercel.com/v1/integrations/deploy/...`)
4. GitHub 저장소 → Settings → Secrets → New secret:
   - Name: `VERCEL_DEPLOY_HOOK_URL`
   - Value: 위 URL
5. Vercel 프로젝트 → Settings → Git → **Production Branch** 영역에서 자동 배포 비활성화 (선택)

이렇게 하면 GitHub Actions가 명시적으로 Vercel에 신호를 보낼 때만 배포.

---

## 🌍 커스텀 도메인 연결

본인 도메인 있으면:

1. Vercel 프로젝트 → Settings → **Domains**
2. 도메인 입력 → Add
3. DNS 설정 안내대로 A 레코드 또는 CNAME 추가
4. 5분~24시간 후 SSL 자동 발급

**가비아·후이즈에서 도메인 산 경우** 각 호스팅사 DNS 관리에서 Vercel이 알려준 값을 그대로 입력하면 끝.

---

## 🧪 로컬 개발 서버

Vercel에 올리기 전 로컬에서 미리 보고 싶으면:

```powershell
# 1. JSON 데이터 생성 (Python)
uv run ai-stock daily

# 2. Next.js 개발 서버 실행
cd web
npm install
npm run dev
```

http://localhost:3000 접속 → 핫 리로드 환경에서 디자인·동작 확인 가능.

---

## 🛠️ 폴더 구조

```
ai-stock/
├── src/ai_stock/                  # Python 분석 파이프라인
│   └── report/
│       └── json_export.py         # JSON 출력 (Next.js용)
├── reports/daily/*.md             # Markdown (백업·기록용)
├── site/                          # 정적 HTML (GitHub Pages, 레거시)
└── web/                           # Next.js 앱 (Vercel)
    ├── app/
    │   ├── page.tsx               # 주식 대시보드
    │   ├── coins/page.tsx         # 코인 대시보드
    │   ├── stock/[ticker]/page.tsx
    │   ├── coin/[ticker]/page.tsx
    │   ├── archive/page.tsx
    │   └── layout.tsx
    ├── components/                # React 컴포넌트
    │   ├── nav.tsx
    │   ├── verdict-matrix.tsx     # 정렬·필터·검색 테이블
    │   ├── focus-cards.tsx
    │   ├── theme-rankings.tsx
    │   ├── twitter-pulse.tsx
    │   ├── search-palette.tsx     # ⌘K 검색
    │   ├── detail-view.tsx
    │   └── ...
    ├── lib/
    │   ├── types.ts               # JSON ↔ TS 타입 정의
    │   ├── data.ts                # 빌드 시 JSON 로드
    │   └── utils.ts
    ├── data/                      # ← Python이 매일 채움
    │   ├── index.json
    │   ├── latest-stock.json
    │   ├── latest-coin.json
    │   ├── stock/YYYY-MM-DD.json
    │   └── coin/YYYY-MM-DD.json
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.ts
    └── next.config.mjs
```

---

## 🆕 새 기능 비교 (vs 기존 GitHub Pages)

| 기능 | GitHub Pages (이전) | **Vercel + Next.js (지금)** |
|---|---|---|
| 종합 판정 매트릭스 | 클릭 정렬만 | **검색 + 4개 필터 + 정렬** |
| 종목 클릭 | (X) | **상세 페이지로 이동** |
| 종목 디테일 페이지 | (없음) | **점수 차트 + LLM 분석 + 외부 링크** |
| ⌘K 검색 팔레트 | (없음) | **있음** (종목/테마 즉시 점프) |
| 코인 트위터 펄스 | 동일 | 동일 + 인터랙티브 |
| 다크/라이트 토글 | 있음 | 있음 (이전 화면 깜빡임 제거) |
| 모바일 UX | OK | **더 매끄러움** (React state) |
| 비공개 저장소 | ❌ | **✅ 무료** |

---

## 🚦 마이그레이션 단계

1. **지금**: 양쪽 동시 운영 (GitHub Pages 그대로 + Vercel 새로)
2. **1~2주 검증**: Vercel 사이트가 안정적으로 매일 갱신되는지 확인
3. **확정 후**: GitHub Pages 배포 끄고 Vercel만 운영
   - `.github/workflows/daily-report.yml`에서 `Upload Pages artifact` + `deploy` job 제거
   - Settings → Pages → Source: None

---

## ❓ FAQ

### Q. Vercel 무료 한도 안에서 운영 가능한가?
A. **네**. Hobby tier 한도(대역폭 100GB/월, 빌드 6,000분/월)에 비해 우리 사용량은 1% 수준. 매일 배포 1회 × 빌드 1~2분 = 월 30~60분.

### Q. Python을 Vercel에서 돌릴 수도 있나?
A. 가능하지만 권장 안 함. 빌드 시간 폭증 + 데이터 fetch 비용 + Anthropic API 호출 위치 분산 → 디버깅 어려움. **GitHub Actions가 데이터 만들고 Vercel이 표시**가 깔끔.

### Q. Vercel이 down되면?
A. GitHub Pages 사이트(`https://homiepark.github.io/ai-stock/`)가 백업으로 계속 동작. Markdown 리포트(`reports/daily/*.md`)는 깃허브에서 직접 열람 가능.

### Q. 비공개 저장소로 바꾸면 Vercel은?
A. ✅ 정상 작동. Vercel Hobby tier가 GitHub 비공개 저장소 자동 지원. **이게 GitHub Pages 대비 가장 큰 실익**.

### Q. 다른 사람과 공유하려면?
A. Vercel URL을 공유하면 됨. 사이트 자체는 공개. 저장소만 비공개로 두는 게 일반적.

---

## 🔧 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| Vercel 빌드: "package.json not found" | Root Directory 설정 안 함 | Settings → Git → **Root Directory: `web`** |
| 데이터 비어있음 ("데이터 준비 중") | GitHub Actions가 아직 안 돌았거나 web/data가 안 커밋됨 | Actions 탭 → 워크플로 수동 실행 또는 로컬에서 `uv run ai-stock daily && git add -f web/data && git commit && git push` |
| 종목 디테일 페이지 404 | `generateStaticParams`가 빈 배열 반환 (데이터 없을 때) | 위 데이터 비어있음 해결 |
| Tailwind 스타일 안 먹음 | `web/app/globals.css` import 누락 | `web/app/layout.tsx`에 `import "./globals.css"` 확인 |
| 한국어 폰트 깨짐 | Pretendard CDN 차단 | `web/app/globals.css`의 `@import` URL 확인 |
