# mdir (Linux TUI File Manager) v0.1.0

> "이 프로젝트는 90년대 DOS 시절 전설적인 파일 관리자였던 최창원 님의 'Mdir'에 대한 오마주(향수)로 제작된 리눅스 TUI 도구입니다."

---

### 📝 개발 노트
구형 노트북에 리눅스 깔았다가 좋기도 하고 불편하기도 해서 Cursor랑 하루 만에 만든 mdir TUI 파일 관리자입니다.

### 📅 내용
엇그제(2026/06/18) 구형 노트북에 우분투 설치하고 파일 보기가 너무 불편해서, 옛날 DOS 시절 Mdir 향수를 담아 Cursor와 함께 뚝딱 만들어 보았습니다. 아직 0.1.0 버전이라 미흡하지만 공유해 봅니다.

---

### 📸 Screenshots
![mdir_screenshot](./image_498ee2.png)

---

### ✉️ Contact
* **Developer:** jsunrise1126
* **Email:** jsunrise1126@gmail.com



Terminal file explorer for Ubuntu/Linux, inspired by Midnight Commander.

## Install

```bash
cd ~/apps/mdir

# If a previous .venv exists but has no activate script, remove it first:
# rm -rf .venv

# Ubuntu minimal installs often lack ensurepip; this still works:
python3 -m venv --without-pip .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If `python3 -m venv` itself fails, install the venv package once:

```bash
sudo apt install python3-venv python3-pip
```

Then recreate the environment:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m mdir
python -m mdir ~/Downloads
```

## Keys

| Key | Action |
|-----|--------|
| Tab | Switch active panel |
| Enter | Open directory / file |
| u / Backspace | Parent directory |
| F2 | Rename |
| F5 | Copy to other panel |
| F6 | Move to other panel |
| F7 | New directory |
| F8 | Delete |
| / | Filter current panel |
| b | Bookmark menu |
| g | Go to bookmark |
| n | Edit with Nono Editor |
| p | Toggle preview pane |
| r | Refresh |
| s | Shell command in current folder |
| v | Edit with Vim Editor |
| q | Quit |

Bookmarks are stored in `~/.config/mdir/bookmarks.json`.

Shell command history (per folder, max 30) is stored in `~/.config/mdir/shell-history.json`.

The layout fills the terminal window and reflows when you resize it.

## WSL (Windows)

mdir runs on **WSL2 + Ubuntu** (same as Linux). Use **Windows Terminal** or `wsl` for best results.

### Option A — inside WSL (recommended)

```bash
git clone https://github.com/jsjang-1126/mdir.git ~/apps/mdir
bash ~/apps/mdir/scripts/install-wsl.sh
source ~/.bashrc
mdir
```

Browse Windows files:

```bash
mdir /mnt/c/Users
mdir /mnt/c/Users/YourName/Downloads
```

### Option B — from Windows PowerShell

```powershell
cd C:\path\to\mdir
powershell -ExecutionPolicy Bypass -File scripts\setup-wsl-from-windows.ps1
```

Then in WSL: `source ~/.bashrc` and `mdir`.

### Option C — Release binary (no Python in WSL)

```bash
wget https://github.com/jsjang-1126/mdir/releases/download/v0.1.0/mdir -O ~/bin/mdir
chmod +x ~/bin/mdir
export PATH="$HOME/bin:$PATH"
mdir
```

**WSL notes:** Use **English input** in Windows Terminal for shortcut keys (`Tab`, `s`, `q`). Optional: `sudo apt install vim nano` for `v` / `n`. `xdg-open` may need `wslu` (`sudo apt install wslu`) to open files in Windows.

## Download (single binary, Linux)

No Python install needed — download `mdir` from [GitHub Releases](https://github.com/jsjang-1126/mdir/releases), then:

```bash
chmod +x mdir
./mdir
```

Optional: move to your PATH, e.g. `mv mdir ~/bin/` or `sudo mv mdir /usr/local/bin/`.

**Note:** The release binary is built for **Linux x86_64**. ARM Mac/PC or Windows need a separate build or use `pip install` from source.

## Build binary (maintainers)

```bash
bash scripts/build-binary.sh
# → dist/mdir  (~14MB, includes Python + Textual)
```
