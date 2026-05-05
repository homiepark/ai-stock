# 본인 전용 사이트 만들기 — GitHub Pages + 자동 업데이트

> 이 가이드를 한 번만 따라하면, 매일 새벽 자동으로 새 리포트가 빌드되어
> **본인 전용 URL**(`https://homiepark.github.io/ai-stock/`)에 올라갑니다.
> 모바일·아이패드 브라우저에서 그 URL만 즐겨찾기 해두면 끝.

---

## 🎯 결과물 미리보기

| 페이지 | 주소 | 내용 |
|---|---|---|
| **메인** | `/index.html` | 오늘의 리포트 (자동으로 최신) |
| **기록** | `/archive.html` | 지난 리포트 날짜별 목록 |
| **각 날짜** | `/2026-05-05.html` | 그날의 리포트 (영구 보존) |

특징:
- ✅ **다크 테마 기본** (밤에 보기 편함, 토글 버튼으로 라이트로 전환)
- ✅ **모바일 최적화** (아이폰·아이패드 모두 깔끔)
- ✅ **표 정렬 가능** (컬럼 헤더 클릭으로 점수순/이름순 정렬)
- ✅ **탭 한 번에 뉴스 원문**
- ✅ **PWA처럼 홈 화면에 추가 가능** (아이폰 Safari "홈 화면에 추가")

---

## 🚀 설정 (한 번만, 약 5분)

### Step 1. ANTHROPIC_API_KEY를 GitHub Secrets에 등록

1. GitHub에서 본인 저장소(`homiepark/ai-stock`) 접속
2. 상단 메뉴 **Settings** 클릭
3. 왼쪽 메뉴 **Secrets and variables → Actions** 클릭
4. 초록색 **"New repository secret"** 버튼 클릭
5. 입력:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Secret**: `sk-ant-...` (본인 키)
6. **Add secret**

### Step 2. GitHub Pages 활성화

1. 같은 **Settings** 안에서 왼쪽 메뉴 **Pages** 클릭
2. **Source** 드롭다운에서 **"GitHub Actions"** 선택
3. 저장 버튼 없음 — 선택 즉시 적용

### Step 3. main 브랜치로 코드 통합 (현재는 작업 브랜치에 있음)

지금 모든 코드는 `claude/ai-investment-analysis-083bm` 브랜치에만 있어요. **main으로 합쳐야** 자동화가 돕니다.

#### 옵션 A: GitHub 웹에서 (가장 쉬움)
1. 저장소 메인 페이지 → 상단 **"Pull requests"** 탭 클릭
2. 초록 **"New pull request"** 클릭
3. 좌측 base: **main**, 우측 compare: **claude/ai-investment-analysis-083bm** 선택
4. **"Create pull request"** → 다음 화면에서 한 번 더 **"Create pull request"**
5. 페이지 아래 초록 **"Merge pull request"** → **"Confirm merge"**

#### 옵션 B: PowerShell에서
```powershell
git checkout main
git merge claude/ai-investment-analysis-083bm
git push
```

### Step 4. 첫 배포 (수동 트리거)

1. 저장소 상단 **Actions** 탭 클릭
2. 왼쪽에서 **"Daily AI Stock Report"** 워크플로 클릭
3. 오른쪽 위 **"Run workflow"** 드롭다운 → **"Run workflow"** 초록 버튼 클릭
4. 30초 후 새로고침 → 새로 생긴 노란 점이 도는 작업 확인
5. 약 3~5분 후 초록 ✓ 두 개 (build + deploy) 뜨면 성공

### Step 5. 사이트 접속

배포된 URL은 두 곳에서 확인 가능:

**A. Settings → Pages** 페이지 상단:
> Your site is live at `https://homiepark.github.io/ai-stock/`

**B. Actions → 방금 그 워크플로 → deploy 단계** 의 url 링크

이 URL을 **모바일/아이패드 브라우저에 즐겨찾기**.

---

## 📱 아이폰/아이패드 홈 화면에 추가 (앱처럼)

1. Safari로 사이트 접속
2. 하단(아이폰) 또는 상단(아이패드) **공유 버튼** (네모+화살표 아이콘) 탭
3. 메뉴에서 **"홈 화면에 추가"**
4. 이름 "AI 주식" 등으로 변경 → 추가
5. 홈 화면에 앱처럼 아이콘 생성 → 탭하면 풀스크린으로 사이트 열림

Android Chrome도 동일하게 "홈 화면에 추가" 가능.

---

## 🕒 자동 업데이트 일정

| 요일 | 한국시간 | 미국 시점 | 업데이트 됨 |
|---|---|---|---|
| 화 | 06:30 | 월요일 마감 후 | 월요일 데이터 반영 |
| 수 | 06:30 | 화요일 마감 후 | 화요일 데이터 반영 |
| 목 | 06:30 | 수요일 마감 후 | 수요일 데이터 반영 |
| 금 | 06:30 | 목요일 마감 후 | 목요일 데이터 반영 |
| 토 | 06:30 | 금요일 마감 후 | 금요일 데이터 반영 |
| 월/일 | (실행 안 함) | 미국장 휴장 | - |

**시간을 바꾸고 싶다면**: `.github/workflows/daily-report.yml` 의 `cron` 라인 수정.

---

## 🛠️ 로컬에서도 사이트 빌드하기

PowerShell에서:

```powershell
uv run ai-stock daily
```

이 한 줄이면:
- `reports\daily\YYYY-MM-DD.md` (Markdown)
- `site\index.html` (HTML 사이트, 매번 최신으로 갱신)
- `site\YYYY-MM-DD.html` (그날 영구 보존)
- `site\archive.html` (목록)

**브라우저로 열어보기**: 파일 탐색기에서 `site\index.html` 더블클릭하면 바로 브라우저로 열림.

또는 VSCode에서 `Live Server` 확장 깔고 `site/index.html` 우클릭 → "Open with Live Server".

---

## 🆘 자주 막히는 곳

| 증상 | 원인 | 해결 |
|---|---|---|
| Actions 워크플로가 안 뜸 | main 브랜치에 .github/workflows/ 가 없음 | Step 3의 main 통합 다시 확인 |
| 워크플로 실행했는데 빨간 X (실패) | API 키 없거나 시크릿 이름 오타 | Step 1 다시. 정확히 `ANTHROPIC_API_KEY` |
| Pages 페이지에 "Source" 없음 | Pages가 비활성화 | Settings → Pages → "GitHub Actions" 선택 |
| 사이트가 404 | 첫 배포 진행 중 | 5~10분 기다린 후 재시도 |
| 사이트는 뜨는데 디자인이 깨짐 | Tailwind CDN 차단 | 회사 네트워크면 개인망에서 시도. 또는 정상 |
| 매일 새벽에 자동 실행 안 됨 | GitHub Actions의 cron은 가끔 지연됨 (최대 1시간) | 정상. 또는 수동 실행 가능 |
| 비공개 저장소인데 사이트가 공개됨 | GitHub Pages는 기본 공개 | 비공개 유지하려면 GitHub Pro 플랜 필요. 무료는 공개 OK |

---

## 🔒 비공개로 쓰고 싶다면

GitHub Pages는 무료 플랜에서 **공개 저장소만 가능**합니다. 옵션:

1. **공개 저장소 + URL 비공유**: 본인 외엔 URL 모르면 안 보이니 사실상 비공개 (Google에 인덱스되지 않게 robots.txt 추가 가능)
2. **GitHub Pro ($4/월)**: 비공개 저장소도 Pages 가능
3. **Vercel/Netlify 무료**: GitHub 비공개 저장소 연결해서 비공개 호스팅 가능 (별도 설정 필요)

대부분 옵션 1로 충분 — URL을 공유 안 하면 됩니다.

---

## ✅ 설정 완료 체크리스트

- [ ] GitHub Secret에 `ANTHROPIC_API_KEY` 등록
- [ ] Settings → Pages → Source: GitHub Actions 선택
- [ ] main 브랜치로 코드 통합 완료
- [ ] Actions 탭에서 "Run workflow" 한 번 수동 실행
- [ ] build + deploy 두 작업 모두 초록 ✓
- [ ] `https://homiepark.github.io/ai-stock/` 접속해서 리포트 확인
- [ ] 아이패드/아이폰에서 홈 화면에 추가
- [ ] 다음 화요일 새벽 06:30 이후 자동 갱신 확인

전부 ✅이면 매일 새 리포트가 자동으로 본인 사이트에 올라옵니다. 아침에 핸드폰으로 확인하면 끝.
