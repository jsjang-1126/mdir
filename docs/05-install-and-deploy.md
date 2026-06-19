# 설치 및 배포

## 1. 로컬 개발 환경 (lg-note / Ubuntu)

### 요구사항
- Python 3.10+
- 터미널 (SSH 포함)

### 설치

```bash
cd ~/apps/mdir

# 깨진 venv가 있으면 삭제
# rm -rf .venv

# Ubuntu minimal (ensurepip 없음)
python3 -m venv --without-pip .venv
source .venv/bin/activate
curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python /tmp/get-pip.py
pip install -r requirements.txt

# 또는 python3-venv 설치 후
# sudo apt install python3-venv python3-pip
# python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

### 어디서든 `mdir` 실행 (PATH)

```bash
pip install -e .

# ~/.bashrc 에 추가
export PATH="$HOME/apps/mdir/.venv/bin:$PATH"

source ~/.bashrc
which mdir   # → .../mdir/.venv/bin/mdir
```

### 개발 모드 (`-e`)
소스 수정 시 재설치 없이 반영됩니다.

---

## 2. 원격 서버 배포 (iwin)

### 서버 정보 (사용자 환경)

| 항목 | 값 |
|------|-----|
| SSH Host 별칭 | `iwin` |
| HostName | `115.68.232.200` |
| User | `root` |
| 키 (Windows) | `C:\Users\jsunr\.ssh\iwin_key` |

### 사전 조건

1. **lg-note**에 SSH config:
   ```
   # ~/.ssh/config
   Host iwin
       HostName 115.68.232.200
       User root
       IdentityFile ~/.ssh/iwin_key
   ```

2. Windows에서 키를 lg-note로 복사 (최초 1회):
   ```powershell
   scp C:\Users\jsunr\.ssh\iwin_key jsunrise1126@lg-note:~/.ssh/iwin_key
   ```

3. lg-note에서:
   ```bash
   chmod 600 ~/.ssh/iwin_key
   ```

### 배포 실행 (lg-note에서)

```bash
bash ~/apps/mdir/scripts/deploy-remote.sh iwin
```

**스크립트 동작:**
1. `rsync`로 `~/apps/mdir` 제외 항목: `.venv`, `__pycache__`, `.git`
2. 원격 `~/apps/mdir`에 업로드
3. `scripts/remote-setup.sh` 실행:
   - `python3 -m venv --without-pip .venv`
   - pip bootstrap + `pip install -e .`
   - `~/.bashrc` / `~/.profile`에 PATH 추가

### iwin에서 사용

```bash
ssh iwin
source ~/.bashrc   # 최초 1회
mdir
```

설치 경로: `/root/apps/mdir`

### 업데이트 배포

로컬에서 코드 수정 후 동일 명령 재실행:
```bash
bash ~/apps/mdir/scripts/deploy-remote.sh iwin
```

---

## 3. Windows에서 직접 iwin 배포 (대안)

lg-note를 거치지 않고 Windows → iwin 직접 배포:

```powershell
# scripts/deploy-from-windows.ps1
# $LgNoteHost = "jsunrise1126@lg-note"  환경에 맞게 수정
.\scripts\deploy-from-windows.ps1
```

Windows에 `iwin_key`가 있을 때 유용.

---

## 4. 의존성 목록

`requirements.txt` / `pyproject.toml`:
```
textual>=0.80.0
rich>=13.0.0
```

시스템 (선택):
```bash
sudo apt install vim nano    # v/n 편집
```

---

## 5. 설정 파일 위치

| 파일 | 경로 |
|------|------|
| 북마크 | `~/.config/mdir/bookmarks.json` |
| SSH (lg-note) | `~/.ssh/config` |
| PATH | `~/.bashrc` |
