# 매일 자동 실행 — 자동화 가이드

> **현재 상태: "ai-stock daily" 명령은 이미 만들어져 있지만, 매일 자동으로 도는 건 아직 아닙니다.** 이 문서대로 한 번 설정하면 그 이후 매일 자동 실행됩니다.

세 가지 방법 중 하나를 고르세요. **GitHub Actions가 가장 추천**(컴퓨터를 켜둘 필요 없음).

---

## 🟢 방법 A: GitHub Actions (추천)

깃허브가 매일 클라우드에서 실행 → 결과를 자동으로 저장소에 커밋 → 핸드폰 깃허브 앱에서 즉시 열람.

**장점**: 컴퓨터 안 켜도 됨. 무료. 실행 로그 깃허브에 남음.
**단점**: 깃허브 비공개 저장소면 무료 한도 월 2,000분(이 프로젝트는 월 60분 정도라 여유).

### 설정 (5분)

**1. ANTHROPIC_API_KEY를 깃허브 시크릿에 등록**
- 저장소 → Settings → Secrets and variables → Actions → New repository secret
- Name: `ANTHROPIC_API_KEY` / Value: `sk-ant-...`

**2. `.github/workflows/daily-report.yml` 파일 추가** (이 저장소에 이미 들어있을 수 있음 — 없으면 아래 내용으로 생성):

```yaml
name: Daily AI Stock Report

on:
  schedule:
    # 한국시간 06:30 = UTC 21:30 (전날). 미국장 마감(NY 16:00 = UTC 21:00) 30분 후
    - cron: '30 21 * * 1-5'
  workflow_dispatch:  # 수동 실행 버튼

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          python-version: '3.11'
      - run: uv sync
      - run: uv run ai-stock daily
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Commit report
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add reports/
          git diff --staged --quiet || git commit -m "daily report $(date +%F)"
          git push
```

**3. 끝.** 저장하면 매주 화~토 한국시간 06:30에 자동 실행. 결과는 `reports/daily/`에.

### 수동 실행
- 저장소 → Actions 탭 → "Daily AI Stock Report" → Run workflow → 즉시 실행.

---

## 🟡 방법 B: macOS 로컬 (launchd)

본인 맥북이 켜져 있을 때 자동 실행.

**1. plist 파일 생성**: `~/Library/LaunchAgents/com.aistock.daily.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.aistock.daily</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>cd /Users/YOURNAME/ai-stock && /opt/homebrew/bin/uv run ai-stock daily && git add reports && git commit -m "daily $(date +%F)" && git push</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>6</integer>
    <key>Minute</key><integer>30</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/aistock-daily.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/aistock-daily.err</string>
</dict>
</plist>
```

`YOURNAME`을 실제 사용자명으로 바꾸세요. uv 경로는 `which uv`로 확인.

**2. 등록**:
```bash
launchctl load ~/Library/LaunchAgents/com.aistock.daily.plist
```

**3. 즉시 테스트**:
```bash
launchctl start com.aistock.daily
tail -f /tmp/aistock-daily.log
```

**해제**: `launchctl unload ~/Library/LaunchAgents/com.aistock.daily.plist`

> ⚠️ **맥북이 자고 있을 때**: launchd가 "Wake the computer" 권한이 필요. **GitHub Actions가 더 안정적**.

---

## 🟠 방법 C: Linux 서버 / Raspberry Pi (cron)

24시간 켜놓는 리눅스 머신이 있다면.

**1. crontab 편집**:
```bash
crontab -e
```

**2. 줄 추가**:
```cron
# 미국장 마감 후 한국시간 06:30 (UTC 21:30, 화~토)
30 21 * * 1-5 cd /home/USER/ai-stock && /home/USER/.local/bin/uv run ai-stock daily >> /tmp/aistock.log 2>&1 && cd /home/USER/ai-stock && git add reports && git commit -m "daily $(date +\%F)" && git push
```

`USER`을 실제 사용자명으로. uv 경로는 `which uv`로 확인.

> **주의**: cron의 `%`는 이스케이프 필요 → `\%`.

**3. 테스트** (한 번만 즉시 실행):
```bash
cd ~/ai-stock && uv run ai-stock daily
```

---

## 🛠️ 실행 시간을 바꾸고 싶다면

| 시점 | UTC | 한국시간 | cron 표현 |
|---|---|---|---|
| 미국장 마감 직후 | 21:30 (전날) | 06:30 (다음날) | `30 21 * * 1-5` |
| 한국장 마감 후 | 06:30 | 15:30 | `30 6 * * 1-5` |
| 매일 정오 (한국) | 03:00 | 12:00 | `0 3 * * *` |

---

## 📱 결과 확인 방법

리포트는 항상 `reports/daily/YYYY-MM-DD.md`에 저장됩니다. 열람 방법:

| 환경 | 방법 |
|---|---|
| **iPhone/Android** | GitHub 앱 → 저장소 → reports/daily/ → 최신 .md 클릭. Markdown 자동 렌더링. |
| **데스크톱 브라우저** | github.com/USER/ai-stock/tree/main/reports/daily 북마크. |
| **노션** | GitHub 레포를 노션에 임포트하거나, 슬랙으로 깃허브 푸시 알림. |
| **로컬** | `cat reports/daily/$(date +%F).md` 또는 VSCode에서 열기. |

---

## ❌ 자동화가 안 도는 흔한 이유

| 증상 | 원인 | 해결 |
|---|---|---|
| 새 리포트 파일 자체가 없음 | API 키 미설정 / cron 설정 실수 | 수동으로 `ai-stock daily` 한 번 돌려 에러 메시지 확인 |
| 리포트는 생기는데 push 안 됨 | git 인증 (PAT/SSH) 미설정 | `git push` 수동 한 번 해서 인증 통과시키기 |
| LLM 서술이 모두 "API 키 미설정" | `.env`에 `ANTHROPIC_API_KEY` 누락 | `.env` 파일 확인. GitHub Actions이면 시크릿 등록 확인 |
| 가격 데이터가 빈 칸 | yfinance/네이버 일시 차단 | `src/ai_stock/cache/` 삭제 후 재실행. 안 되면 다음 날 재시도 |
| 같은 리포트가 두 번 생성 | 시간대 혼동 | UTC 기준으로 짜야 함. 한국시간 ≠ UTC |

---

## 🚦 자동화 전 체크리스트

자동화 걸기 전에 한 번은 수동으로 돌려보고 다음을 확인하세요:

- [ ] `cp .env.example .env` → API 키 입력 완료
- [ ] `uv run ai-stock daily` 수동 실행 → `reports/daily/YYYY-MM-DD.md` 생성 확인
- [ ] 리포트 본문에 LLM 서술이 있고 "API 키 미설정" 메시지가 없음
- [ ] `git status`로 reports/ 변경분 확인 → `git push`로 한 번 푸시 성공
- [ ] 위 4개가 OK면 → 자동화 설정 진행

체크리스트가 통과되어야 자동화도 안정적으로 돕니다.
