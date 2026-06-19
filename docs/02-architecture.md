# 아키텍처 및 재구현 가이드

다른 AI가 **동일한 mdir**을 처음부터 만들 때 참고하는 기술 문서입니다.

---

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.10+ |
| TUI 프레임워크 | [Textual](https://textual.textualize.io/) ≥ 0.80 |
| 텍스트 렌더링 | Rich (Syntax 하이라이트) |
| 패키징 | setuptools + `pyproject.toml` |
| 진입점 | `mdir = mdir.__main__:main` |

---

## 디렉터리 구조

```
mdir/
├── pyproject.toml
├── requirements.txt
├── README.md
├── docs/                    # 이 문서들
├── scripts/
│   ├── deploy-remote.sh     # lg-note → iwin rsync 배포
│   ├── remote-setup.sh      # 원격 venv + pip install + PATH
│   └── deploy-from-windows.ps1
└── mdir/
    ├── __init__.py          # __version__
    ├── __main__.py          # argparse, main()
    ├── app.py               # MdirApp (App 서브클래스)
    ├── models.py            # FileEntry, list_directory
    ├── operations.py        # 파일 시스템 작업
    ├── bookmarks.py         # JSON 북마크 저장
    ├── preview.py           # PreviewPane, is_text_file
    ├── widgets.py           # FilePanel, CenterModal, InputModal, ChoiceModal
    └── mdir.tcss            # Screen 레이아웃
```

---

## 화면 레이아웃 (compose)

```
┌─ Screen (vertical) ─────────────────────────────────────────┐
│ ┌─ #main-layout (horizontal, height: 1fr) ────────────────┐ │
│ │ ┌─ #panels (2fr) ─────┐ ┌─ #preview-pane (1fr) ───────┐ │ │
│ │ │ FilePanel left      │ │ PreviewPane                 │ │ │
│ │ │ FilePanel right     │ │                             │ │ │
│ │ └─────────────────────┘ └─────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────┘ │
│ #status-bar (height: 1)                                       │
│ #help-bar (height: 1)                                         │
│ Footer (Textual 기본 단축키 표시)                              │
└───────────────────────────────────────────────────────────────┘

모달 열릴 때: CenterModal (overlay, align center) + InputModal | ChoiceModal
```

### CSS 핵심 (`mdir.tcss`)

- `#main-layout`, `#panels`, `#preview-pane`: `height: 1fr; min-height: 1`
- `FilePanel`: `width: 1fr`, `border: solid`, `.active` 시 `border: heavy $success`
- **금지 패턴**: 빈 `Container`에 `width/height: 100%` overlay — 전체 UI 가림

---

## 클래스 책임

### `MdirApp` (`app.py`)

- `BINDINGS`: 전역 단축키
- `_active_panel_id`: 현재 선택 패널 (`left-panel` | `right-panel`)
- `_modal_return_panel_id`: 모달 열기 전 패널 (닫을 때 포커스 복원)
- `_set_active_panel()`: 테두리(active) + `set_focus(DataTable)`
- `_modal_mount()`: `CenterModal(widget, return_panel_id)` 마운트
- `_guard_modal()`: 모달 열릴 때 탐색 단축키 차단

### `FilePanel` (`widgets.py`)

- `DataTable`로 디렉터리 목록
- reactive: `current_path`, `filter_text`, `active`
- `on_data_table_row_selected` / `action_open_selected`: Enter로 진입
- `refresh_listing()`: `list_directory()` → 테이블 갱신

### `FileEntry` (`models.py`)

```python
@dataclass
class FileEntry:
    path: Path
    name: str
    is_dir: bool
    size: int
    modified: float  # st_mtime
    mode: int
```

- `list_directory(path)`: `..` 항목 + 정렬된 자식 목록
- `modified_text`: 패널용 `%Y-%m-%d %H:%M`
- `modified_detail_text`: 상태바용 `%Y-%m-%d %H:%M:%S`

### `operations.py`

- `copy_item`, `move_item`, `delete`, `mkdir`, `rename`
- `unique_destination()`: 이름 충돌 시 `name (1).ext` 생성

### `bookmarks.py`

- 저장 위치: `~/.config/mdir/bookmarks.json`
- `load_bookmarks`, `save_bookmarks`, `add_bookmark`, `remove_bookmark`

### `preview.py`

- `PreviewPane.show_path(path)`: 텍스트는 Rich Syntax, 바이너리는 크기만
- `is_text_file(path)`: 확장자 + null 바이트 검사

### 모달 (`widgets.py`)

| 클래스 | 용도 |
|--------|------|
| `CenterModal` | 투명 전체 오버레이, 자식 중앙 정렬 |
| `ChoiceModal` | 목록 선택 (북마크 메뉴, 삭제 확인) |
| `InputModal` | 한 줄 입력 (이름, 필터, 북마크 이름) |

**모달 닫기:** `_close_modal_dialog()` → host `CenterModal.remove()` → `restore_panel_after_modal()`

---

## 데이터 흐름

### 파일 선택 (마우스/키보드)

```
DataTable RowHighlighted
  → FilePanel.SelectionChanged
  → MdirApp.on_panel_selection
  → PreviewPane.show_path + status-bar 갱신
```

### 복사 (F5)

```
active_panel.selected_entry
  → copy_item(source, inactive_panel.current_path)
  → inactive_panel.refresh_listing()
```

### vim 편집 (v)

```
_selected_text_file() → is_text_file 검사
  → with self.suspend(): subprocess.call(["vim", path])
  → 양쪽 패널 refresh_listing()
```

`suspend()`는 Textual UI를 잠시 내리고 같은 터미널에서 외부 프로그램 실행.

---

## 재구현 체크리스트 (AI용)

1. [ ] `pyproject.toml` + `requirements.txt` (textual, rich)
2. [ ] `FileEntry` + `list_directory` with `..`
3. [ ] `FilePanel` + DataTable 4컬럼
4. [ ] `MdirApp` 2패널 + Preview + status/help bar
5. [ ] F5/F6/F7/F8/F2 파일 작업
6. [ ] 북마크 JSON + b/g 메뉴
7. [ ] `CenterModal` — **전체 덮는 불투명 레이어 사용 금지**
8. [ ] Enter: FilePanel에서 처리 + ChoiceModal priority 바인딩
9. [ ] 모달 닫을 때 `_modal_return_panel_id` + 지연 `set_focus`
10. [ ] InputModal: CenterModal이 Input 포커스 탈취하지 않게
11. [ ] v/n + `App.suspend()`
12. [ ] `pip install -e .` + entry point `mdir`
13. [ ] 배포 스크립트 (선택)
