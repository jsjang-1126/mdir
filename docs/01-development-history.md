# 개발 히스토리: 요구사항 → 작업 → 결과

이 문서는 사용자와 AI(Cursor)가 나눈 대화를 시간 순으로 정리한 것입니다.

---

## 1단계: 아이디어 및 가능성 확인

### 사용자 요구
> Ubuntu 환경에서 윈도우 탐색기 같은 프로그램을 **텍스트 화면(TUI)** 으로 만들 수 있을까?

### AI 작업
- TUI 파일 탐색기의 가능성 설명
- 기존 참고 프로그램 소개: `ranger`, `nnn`, `lf`, `mc`, `vifm`
- 구현 난이도 4단계 제시 (단일 패널 → 2패널 → 미리보기/북마크 → 고급)
- 기술 스택 후보: Python+Textual, Rust+ratatui, Go+tview 등
- 워크스페이스 `~/apps/mdir` 폴더가 비어 있음을 확인

### 결과
- **가능함**을 확인하고, Python + Textual 추천
- 사용자가 언어 선택을 맡김

---

## 2단계: 프로젝트 생성 (핵심 구현)

### 사용자 요구
> Python + Textual로 `mdir` 폴더에 만들어 달라.  
> 4단계(미리보기, 검색, 북마크, 터미널 크기 대응)까지 해 달라.  
> 터미널 리사이즈는 **전체 화면을 채우는 정도**면 충분하다.

### AI 작업
다음 파일·구조를 생성:

```
mdir/
├── requirements.txt
├── pyproject.toml
├── README.md
├── scripts/          (후에 배포 스크립트 추가)
└── mdir/
    ├── __init__.py
    ├── __main__.py
    ├── app.py          # 메인 앱, 단축키, 액션
    ├── models.py       # FileEntry, list_directory
    ├── operations.py   # 복사/이동/삭제/이름변경/mkdir
    ├── bookmarks.py    # ~/.config/mdir/bookmarks.json
    ├── preview.py      # 텍스트 미리보기
    ├── widgets.py      # FilePanel, 모달
    └── mdir.tcss       # 레이아웃 CSS
```

**구현한 기능:**
- 2패널 파일 목록 (`DataTable`: Name, Size, Modified, Perm)
- Tab 패널 전환, Enter 폴더 진입/파일 열기 (`xdg-open`)
- F5 복사, F6 이동, F7 mkdir, F8 삭제, F2 이름 변경
- `/` 필터 검색
- `b` 북마크 메뉴, `g` 북마크 이동
- `p` 미리보기 패널 토글
- `r` 새로고침, `q` 종료
- Textual `1fr` 레이아웃으로 터미널 크기에 맞춤

### 결과
- v0.1.0 기본 탐색기 완성
- Ubuntu minimal 환경에서 `pip`/`venv` 없음 → 설치 가이드만 제공

---

## 3단계: 로컬 환경 설치 문제

### 사용자 요구
> `source .venv/bin/activate` 실패. `.venv/bin`에 python만 있고 activate 없음.

### AI 작업
- 원인: `python3-venv`/`ensurepip` 없이 venv가 **반쯤만** 생성됨
- 해결:
  ```bash
  rm -rf .venv
  python3 -m venv --without-pip .venv
  .venv/bin/python get-pip.py
  pip install -r requirements.txt
  ```
- README에 Ubuntu용 설치 절차 추가

### 결과
- 로컬에서 `python -m mdir` 실행 가능

---

## 4단계: 실행 시 크래시 (빈 화면)

### 사용자 요구
> 에러: `NoMatches: No nodes match '.panel-path' on FilePanel`  
> 이후: 에러는 없는데 **아무것도 안 보임** (Footer만 보임)

### AI 작업

**버그 A — `__init__`에서 reactive 설정**
- `FilePanel.__init__`에서 `current_path` 설정 → `watch_current_path`가 UI 마운트 전 호출
- 수정: `_initial_path` 저장 후 `on_mount()`에서 `current_path` 설정

**버그 B — modal-layer가 화면 전체 덮음**
- `#modal-layer { width: 100%; height: 100%; }` 가 빈 오버레이로 전체 UI 가림
- 수정: modal-layer 제거, 모달만 `layer: overlay`로 마운트

### 결과
- 2패널 + 미리보기 + 상태바 정상 표시

---

## 5단계: 북마크 모달 UX 버그 (연속 수정)

### 사용자 요구 (순서대로)
1. 북마크 창이 **좌측 상단**에 작게 뜨고 **안 없어짐**
2. `↑↓`, `c`, `Esc`는 되는데 **Enter는 안 됨**
3. Enter로 폴더 진입이 **안 됨** (북마크 수정 후)
4. 북마크 닫으면 **패널1 테두리인데 키는 패널2**에서 먹음
5. Add bookmark → 이름 입력 화면에서 **Enter가 안 먹고 Esc만 됨**

### AI 작업 요약

| 문제 | 원인 | 해결 |
|------|------|------|
| 모달 위치/미닫힘 | 포커스 없음, 중앙 정렬 없음 | `CenterModal` + `can_focus` + 클릭 처리 |
| Enter가 메뉴에서 안 닫힘 | App `open_entry`가 Enter 가로챔 | `ChoiceModal`에 `priority=True` Enter 바인딩 |
| 폴더 Enter 안 됨 | DataTable이 Enter 처리, App 바인딩 무력 | `FilePanel.on_data_table_row_selected` + `action_open_selected` |
| 포커스 패널2 고정 | 모달 닫힌 뒤 Textual이 포커스 재할당 | `_modal_return_panel_id` 저장, `set_focus` + `set_timer` 지연 복원 |
| 이름 입력 Enter 안 됨 | `CenterModal.on_mount`가 Input 포커스 탈취 | CenterModal에서 dialog.focus() 제거, Input에 `call_after_refresh` 포커스 |

### 결과
- 북마크 전체 플로우 안정화
- Add bookmark: 이름 입력 → Enter 저장 → 메인 복귀

---

## 6단계: 기능 추가

### 사용자 요구 → 작업

| 요구 | 작업 |
|------|------|
| 하단 상태바에 **수정 일시** 표시 | `FileEntry.modified_detail_text` (`YYYY-MM-DD HH:MM:SS`) 추가 |
| 텍스트 파일 `v` → vim, `n` → nano | `App.suspend()` + `subprocess.call([editor, path])`, `is_text_file()` 판별 |
| 셸 어디서든 `mdir` 실행 | `pip install -e .` + `~/.bashrc` PATH 등록 |
| **iwin** 서버에 배포 | SSH config, `deploy-remote.sh`, Windows 키 복사 후 rsync 배포 |

---

## 7단계: 원격 배포 (iwin)

### 사용자 요구
> Windows `.ssh/config`의 `iwin` 서버에 실행 파일 넣고 실행 가능하게

### 환경 제약
- AI 실행 환경은 **lg-note (Linux)** — Windows `C:\Users\...` 직접 접근 불가
- lg-note에 `iwin_key` 없음 → SSH 실패

### AI 작업
1. lg-note `~/.ssh/config` 작성:
   ```
   Host iwin
       HostName 115.68.232.200
       User root
       IdentityFile ~/.ssh/iwin_key
   ```
2. `scripts/deploy-remote.sh`, `scripts/remote-setup.sh`, `scripts/deploy-from-windows.ps1` 작성
3. 사용자가 Windows에서 키 복사:
   ```powershell
   scp C:\Users\jsunr\.ssh\iwin_key jsunrise1126@lg-note:~/.ssh/iwin_key
   ```
4. `bash scripts/deploy-remote.sh iwin` 실행 → `/root/apps/mdir` 설치 완료

### 결과
- iwin에서 `mdir` 명령 사용 가능

---

## 개발 일정 요약 (대화 세션 기준)

| 순서 | 주제 | 산출물 |
|------|------|--------|
| 1 | TUI 탐색기 가능성 | 기술 조사, 스택 제안 |
| 2 | mdir 1차 구현 | 전체 패키지 v0.1.0 |
| 3 | venv 수정 | `--without-pip` 설치 절차 |
| 4 | UI 버그 | reactive/mount, modal-layer 수정 |
| 5 | 북마크/포커스 | 모달·Enter·포커스 복원 |
| 6 | vim/nano, 상태바, PATH | 편집기 연동, 배포 준비 |
| 7 | iwin 배포 | 원격 설치 스크립트 |
