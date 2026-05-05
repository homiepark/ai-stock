# 환경 설정 — 0부터 시작 (VSCode 기준)

> **터미널이 뭔지도 모르는 분 환영.** 한 단계씩 따라하면 됩니다. Mac / Windows 둘 다 커버.
> 처음 한 번만 30분~1시간. 이후엔 명령어 두세 줄이면 끝.

---

## 🤔 먼저, 어디서 작업하나?

**답: VSCode 안의 터미널(Terminal)에서 다 합니다.**

- VSCode = 코드 편집기 (Microsoft가 만든 무료 프로그램)
- 그 안에 **터미널**이라는 검은 창이 내장되어 있어, 명령어를 입력하면 컴퓨터가 실행
- 이 프로젝트의 모든 작업(설치·실행·리포트 생성)은 그 터미널에서 명령어 한 줄씩 입력하는 방식

VSCode가 없어도 OS의 기본 터미널(Mac=Terminal, Windows=PowerShell)에서 똑같이 됩니다. **VSCode를 쓰면 편한 이유**: 코드 보기 + 터미널 + Markdown 리포트 미리보기를 한 화면에서 다 볼 수 있음.

---

## 🍎 Mac 사용자

### Step 1. 사전 준비 (한 번만)

**Mac의 기본 Terminal 앱 열기** (Spotlight `⌘+Space` → "Terminal" 검색)

아래를 복사해서 붙여넣고 Enter:

```bash
# 1. Homebrew (Mac용 패키지 매니저) — 이미 깔려있으면 건너뛰기
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 필수 도구 3개
brew install git python@3.11 uv

# 3. VSCode (이미 있으면 건너뛰기)
brew install --cask visual-studio-code
```

각 명령어 후 비밀번호를 물으면 Mac 로그인 비밀번호 입력. 화면에 글자 안 보여도 정상 (보안).

설치 확인:
```bash
git --version    # git version 2.x.x
python3 --version  # Python 3.11.x 이상
uv --version     # uv 0.x.x
```

### Step 2. 프로젝트 받아오기

원하는 폴더에 받기. 기본은 Documents:

```bash
cd ~/Documents
git clone https://github.com/homiepark/ai-stock.git
cd ai-stock
```

### Step 3. VSCode에서 폴더 열기

```bash
code .
```

(처음 `code` 명령어가 안 먹히면: VSCode 실행 → `⌘+Shift+P` → "Shell Command: Install 'code' command in PATH" 검색 → 클릭)

또는 VSCode 실행 → File → Open Folder → `ai-stock` 폴더 선택.

### Step 4. VSCode 안에서 터미널 열기

상단 메뉴: **Terminal → New Terminal**
단축키: `` ⌃+` `` (Control + 백틱)

화면 아래에 검은 창이 뜨면 그게 터미널. **이제부터 모든 명령어는 여기**.

### Step 5. API 키 설정

VSCode 왼쪽 파일 트리에서:
1. `.env.example` 우클릭 → "Copy"
2. 빈 곳 우클릭 → "Paste" (`.env.example copy`라는 이름이 생김)
3. 그 파일 우클릭 → "Rename" → `.env`로 변경

또는 터미널에서 한 줄:
```bash
cp .env.example .env
```

`.env` 클릭해서 열고:

```
ANTHROPIC_API_KEY=sk-ant-여기에_본인_키
```

**API 키 발급 방법**:
1. https://console.anthropic.com 접속 → 가입
2. Settings → API Keys → "Create Key"
3. `sk-ant-...`으로 시작하는 키 복사
4. 결제카드 등록 후 $5~10 충전 (이 프로젝트는 한 달 $3~10 정도)

저장 (`⌘+S`).

### Step 6. 라이브러리 설치 + 첫 실행

VSCode 터미널에서:

```bash
uv sync                # 1~2분
uv run ai-stock daily
```

### Step 7. 리포트 보기

VSCode 왼쪽 파일 트리에서 `reports/daily/` 폴더 → 오늘 날짜 `.md` 파일 클릭.

오른쪽 위에 **책 모양 아이콘** (Open Preview to the Side)이 보입니다. 그걸 누르면 Markdown이 예쁘게 렌더링됨.

축하합니다 🎉 — 첫 리포트 완료.

---

## 🪟 Windows 사용자 (자세한 가이드)

> Windows에서는 **PowerShell**이라는 터미널을 씁니다. 이 가이드대로만 하면 됩니다.

### Step 1. 사전 준비 4가지 설치 (한 번만, 약 15분)

#### 1-1. VSCode 설치
1. https://code.visualstudio.com/ 접속
2. 파란 "Download for Windows" 버튼 클릭
3. 다운로드된 `VSCodeUserSetup-x64-*.exe` 더블클릭
4. 설치 옵션에서 **"Add to PATH"**, **"Open with Code 추가"** 등 모든 체크박스 켜기
5. 설치 완료 → "Launch Visual Studio Code" 체크하고 마침

#### 1-2. Python 설치
1. https://www.python.org/downloads/ 접속
2. 노란 "Download Python 3.x.x" 버튼 클릭 (3.11 이상이면 OK)
3. 다운로드된 `python-*.exe` 더블클릭
4. **🚨 매우 중요**: 첫 화면 맨 아래 **"Add python.exe to PATH"** 체크박스 반드시 켜기
5. "Install Now" 클릭
6. 설치 완료 후 "Close"

#### 1-3. Git 설치
1. https://git-scm.com/download/win 접속 → 자동으로 설치 파일 다운로드 시작
2. `Git-*.exe` 더블클릭
3. 모든 옵션 **기본값 그대로** Next 연타 (10번 정도 누르면 끝)
4. 설치 완료 → Finish

#### 1-4. uv 설치
1. **시작 메뉴** → "PowerShell" 검색 → **"Windows PowerShell"** 우클릭 → **"관리자 권한으로 실행"**
2. "이 앱이 디바이스를 변경할 수 있도록 허용..." → **예**
3. 파란색 PowerShell 창에 아래 한 줄 복붙 → Enter:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

4. 설치 끝나면 PowerShell 창 닫기 (`exit` 입력 또는 X 버튼)

#### 1-5. 설치 확인
**PowerShell을 새로 열고** (관리자 권한 아니어도 OK) 아래 4줄을 한 줄씩 입력:

```powershell
code --version
python --version
git --version
uv --version
```

각각 버전 번호가 뜨면 성공. **"command not found" 또는 "인식되지 않습니다"가 뜨면**:
- PowerShell을 완전히 닫고 새로 열기
- 그래도 안 되면 컴퓨터 재시작

### Step 2. 프로젝트 받아오기

PowerShell에서:

```powershell
cd $HOME\Documents
git clone https://github.com/homiepark/ai-stock.git
cd ai-stock
```

> **Tip**: `git clone` 시 사용자명·비밀번호를 물으면, 비밀번호 자리에 GitHub의 **Personal Access Token (PAT)** 을 입력해야 합니다 (그냥 비밀번호는 안 됨). PAT 발급: https://github.com/settings/tokens → "Generate new token (classic)" → repo 권한만 체크 → 생성된 토큰 복사. 비공개 저장소 아니라면 인증 안 물을 수도 있음.

### Step 3. VSCode로 폴더 열기

```powershell
code .
```

**주의**: 점(`.`) 빼먹지 말기. "현재 폴더를 VSCode로 열기"라는 뜻.

### Step 4. VSCode 안에서 터미널 열기

1. 상단 메뉴 **Terminal → New Terminal**
2. 단축키: `` Ctrl+` `` (Ctrl + 백틱; 백틱은 보통 `1` 키 왼쪽의 `~` 키)
3. 화면 아래에 검은 창이 뜨면 그게 터미널 (PowerShell이 실행됨)

**여기서부터 모든 명령어는 이 VSCode 터미널 창에서 실행**.

### Step 5. API 키 설정

#### 방법 A: VSCode UI로
1. 왼쪽 파일 트리에서 `.env.example` 마우스 오른쪽 클릭 → **Copy**
2. 빈 곳 마우스 오른쪽 클릭 → **Paste** (`.env.example copy`라는 이름의 파일이 생김)
3. 그 파일 마우스 오른쪽 클릭 → **Rename** → 이름을 `.env`로 변경 (앞에 점 잊지 말기)

#### 방법 B: 터미널로 (한 줄)
```powershell
Copy-Item .env.example .env
```

#### `.env` 파일에 키 넣기
1. 왼쪽 트리에서 `.env` 클릭하면 오른쪽에 파일이 열림
2. 첫 줄 수정:

```
ANTHROPIC_API_KEY=sk-ant-여기에_본인_키_붙여넣기
FRED_API_KEY=optional_for_macro_data
```

3. `Ctrl+S` 로 저장

#### 🔑 API 키 발급 (처음이면)
1. https://console.anthropic.com 접속 → 가입 (Google 계정 가능)
2. 왼쪽 메뉴 **Settings** → **API Keys** → **Create Key**
3. 키 이름 적당히 (예: "ai-stock") → Create
4. **`sk-ant-...`로 시작하는 키 복사** (한 번만 보여줌, 못 복사하면 키 다시 만들어야 함)
5. **결제 카드 등록**: 왼쪽 메뉴 **Plans & Billing** → 카드 등록 + $5~10 충전
   - 이 프로젝트는 한 달 약 $3~10 사용 예상

### Step 6. 라이브러리 설치 + 첫 실행

VSCode 터미널에서 (PowerShell 창에서):

```powershell
uv sync
```

50개 패키지 설치, 1~2분 소요. 빨간 글자 없이 끝나면 OK.

```powershell
uv run ai-stock daily
```

50종목 분석, 1~3분 소요. 끝나면 마지막 줄에:
```
리포트 생성 완료: reports\daily\2026-XX-XX.md
```

### Step 7. 리포트 보기

1. VSCode 왼쪽 파일 트리에서 `reports` 폴더 펼치기 → `daily` 폴더 펼치기
2. 오늘 날짜 `.md` 파일 클릭 (예: `2026-05-05.md`)
3. **오른쪽 위에 책 모양 아이콘 (Open Preview to the Side)** 클릭
   - 단축키: `Ctrl+K` 누르고 `V`
4. 오른쪽에 예쁘게 렌더링된 리포트가 뜸

🎉 **여기까지 됐다면 환경 설정 완료**.

### Step 8. 다음에 다시 실행할 때

VSCode 다시 켜고 → File → Open Recent → ai-stock → 터미널 열고:

```powershell
uv run ai-stock daily
```

이거 한 줄이면 끝. 매일 이거만 입력하면 새 리포트 생성. (Step 1~5는 처음 한 번만)

---

## 🆘 Windows에서 자주 막히는 곳

| 증상 | 원인 | 해결 |
|---|---|---|
| `python: command not found` 또는 `python을 찾을 수 없습니다` | Python 설치 시 "Add to PATH" 체크 안 함 | Python 재설치, **첫 화면 맨 아래 체크박스 반드시 켜기** |
| `uv : 인식되지 않습니다` | uv 설치 후 PowerShell 새로 안 열음 | PowerShell 완전 닫고 새로 열기. 안 되면 재부팅 |
| `git clone` 시 SSL/인증 에러 | 회사 네트워크 또는 백신이 차단 | 개인망에서 시도하거나, GitHub Desktop 앱(https://desktop.github.com)으로 클론 |
| `uv sync`에서 `pykrx` 빌드 실패 | C++ 빌드 도구 부재 | https://visualstudio.microsoft.com/visual-cpp-build-tools/ 설치 후 재시도 |
| `code .`이 안 됨 | VSCode 설치 시 PATH 미추가 | VSCode 실행 → `Ctrl+Shift+P` → "Shell Command: Install 'code' command in PATH" 검색하여 클릭 |
| `.env` 파일이 안 보임 | 숨김 파일 (점으로 시작) | VSCode 트리에는 보임. Windows 탐색기에서는 "보기" → "숨김 항목" 체크 |
| API 키 넣었는데 LLM 서술이 "API 키 미설정" | `.env` 파일이 잘못된 위치 또는 따옴표 포함 | `.env`가 `pyproject.toml`과 같은 폴더(루트)에 있는지 + `ANTHROPIC_API_KEY=sk-ant-...` 형식 (따옴표 X, 공백 X) |
| 리포트 표가 깨져 보임 | Markdown 미리보기 안 켬 | `.md` 파일 열고 `Ctrl+K` 다음 `V` |
| `uv run` 시 권한 거부 | PowerShell 실행 정책 | PowerShell 관리자 권한으로 열고: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## 🆘 자주 막히는 곳

| 증상 | 원인 | 해결 |
|---|---|---|
| `command not found: uv` | 터미널이 uv 설치 후 새로 안 열림 | 터미널 닫고 다시 열기 (Mac: `⌘+Shift+P` → "Kill Terminal") |
| `command not found: brew` | Apple Silicon Mac에서 PATH 안 잡힘 | `echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile && source ~/.zprofile` |
| `git clone` 시 인증 요구 | 비공개 저장소면 권한 필요 | 저장소가 본인 깃허브인지 확인. 비공개면 GitHub Desktop으로 클론이 더 쉬움 |
| `uv sync` 중 에러 | Python 3.11 미만 | `python3 --version` 확인. 3.11+ 필요 |
| `.env`에 키 넣었는데 LLM 서술이 "API 키 미설정" | `.env` 파일이 ai-stock 폴더 **루트**가 아닌 다른 곳에 있음 | VSCode 왼쪽 트리에서 `.env`가 `pyproject.toml`과 **같은 줄**에 있는지 확인 |
| Anthropic 결제 미설정 | API 키만 만들고 결제카드 등록 안 함 | console.anthropic.com → Plans & Billing → 카드 등록 + $5 충전 |
| reports 폴더가 비어있음 | `ai-stock daily` 실행이 도중에 멈췄거나 에러 | 터미널의 빨간 글자 메시지 읽고 → 모르면 그 메시지를 그대로 검색 |

---

## 🧭 VSCode를 처음 쓴다면 — 꼭 알면 좋은 단축키

| 단축키 (Mac) | 단축키 (Win) | 기능 |
|---|---|---|
| `⌘+Shift+P` | `Ctrl+Shift+P` | 명령 팔레트 (모든 기능 검색) |
| `` ⌃+` `` | `` Ctrl+` `` | 터미널 열기/숨기기 |
| `⌘+P` | `Ctrl+P` | 파일 빠른 열기 |
| `⌘+S` | `Ctrl+S` | 저장 |
| `⌘+B` | `Ctrl+B` | 왼쪽 파일 트리 토글 |
| `⌘+K V` | `Ctrl+K V` | Markdown 미리보기 (옆 창) |

**추천 확장**:
- "Python" (Microsoft) — 코드 자동완성·문법 검사
- "Markdown All in One" — 리포트 .md 파일 보기 편함

---

## ✅ 환경 설정 완료 체크리스트

- [ ] VSCode 열고 `ai-stock` 폴더 보임
- [ ] VSCode 안에서 터미널 열림 (`` ⌃+` ``)
- [ ] 터미널에서 `uv --version` 입력 → 버전 번호 나옴
- [ ] 왼쪽 트리에 `.env` 파일 있음 (점 찍힌 파일)
- [ ] `.env` 안에 본인 ANTHROPIC_API_KEY 입력 + 저장
- [ ] `uv sync` 실행 → 에러 없이 완료
- [ ] `uv run ai-stock daily` 실행 → reports/daily/ 에 .md 파일 생김
- [ ] 그 .md 파일 열고 Top 5 종목에 LLM이 작성한 한국어 분석 보임

여기까지 됐다면 모든 환경 설정 완료. 그 다음은 [docs/NEXT_STEPS.md](NEXT_STEPS.md) 의 Step 2~4로.

---

## ❓ 더 막히면

이 파일에 안 적힌 막힘 발생 시 → 터미널에 뜬 **빨간 메시지를 그대로 검색**하면 거의 답이 나옵니다.

핵심 명령어 5개만 외우면 평생 씁니다:
- `cd <폴더>` — 폴더 이동
- `ls` (Win: `dir`) — 현재 폴더 파일 목록
- `code .` — 현재 폴더를 VSCode로 열기
- `uv sync` — 라이브러리 설치
- `uv run ai-stock daily` — 리포트 생성
