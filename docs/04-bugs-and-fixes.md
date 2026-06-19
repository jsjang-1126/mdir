# 버그와 수정 — Textual TUI 개발 시 교훈

mdir 개발 중 실제로 발생한 문제와 해결책입니다. **같은 실수를 반복하지 않기 위한** 레퍼런스입니다.

---

## 1. reactive 속성을 `__init__`에서 설정

### 증상
```
NoMatches: No nodes match '.panel-path' on FilePanel
```

### 원인
`current_path`를 `__init__`에서 설정 → `watch_current_path`가 `compose()` 전에 실행 → Label 위젯 없음.

### 해결
```python
def __init__(...):
    self._initial_path = path.resolve()  # reactive 건드리지 않음

def on_mount(self):
    self.current_path = self._initial_path  # UI 준비 후 설정
```

### watch 가드 (추가 안전)
```python
def watch_current_path(self, _path):
    if not self.is_attached:
        return
    ...
```

---

## 2. 빈 overlay Container가 전체 화면 가림

### 증상
앱은 실행되지만 메인 영역이 검은색, Footer만 보임.

### 원인
```css
#modal-layer {
    layer: overlay;
    width: 100%;
    height: 100%;
}
```
빈 Container도 레이아웃·페인팅에 참여해 본문을 가림.

### 해결
- 상시 full-screen modal host **제거**
- 모달 필요 시에만 `CenterModal` 마운트
- `CenterModal`은 `align: center middle`만, 자식 크기는 `auto`

---

## 3. App 단축키가 모달 Enter를 가로챔

### 증상
북마크 메뉴에서 Enter → 창 안 닫힘, 뒤에서 파일 열기 등 이상 동작.

### 원인
```python
Binding("enter", "open_entry", priority=True)  # App 레벨
```

### 해결
- App `enter`에서 `priority=True` **제거**
- `ChoiceModal`에 `Binding("enter", "confirm_choice", priority=True)`
- `_guard_modal()`로 모달 열릴 때 App 액션 early return

---

## 4. DataTable Enter vs App `open_entry`

### 증상
폴더에서 Enter로 진입이 안 됨.

### 원인
포커스가 DataTable에 있을 때 App `open_entry`가 호출되지 않음.

### 해결
FilePanel에서 직접 처리:
```python
def on_data_table_row_selected(self, event):
    self.activate_selection()

BINDINGS = [Binding("enter", "open_selected", priority=True)]
```

---

## 5. 모달 닫은 뒤 포커스가 다른 패널로

### 증상
패널1 연두 테두리인데 키 입력은 패널2에서 동작.

### 원인
- `active` (CSS 클래스) ≠ 키보드 `focus` (DataTable)
- 모달 제거 후 Textual이 포커스를 DOM 순서상 마지막 테이블로 복원

### 해결
```python
# 모달 열 때
self._modal_return_panel_id = self._active_panel_id

# 모달 닫을 때 (CenterModal 제거 후)
def restore_panel_after_modal(self, panel_id):
    def restore():
        if self._modal_open():
            return
        self._set_active_panel(panel_id)
    self.call_later(restore)
    self.set_timer(0.05, restore)  # Textual 자동 포커스 이후 실행

def _set_active_panel(self, panel_id):
    self._active_panel_id = panel_id
    # active 클래스 갱신 ...
    self.set_focus(self.query_one(f"#{panel_id}-table", DataTable))
```

**핵심:** 테두리와 포커스를 **항상 같이** 맞출 것.

---

## 6. CenterModal이 Input 포커스 탈취

### 증상
북마크 이름 입력에서 Enter 안 됨, Esc만 됨.

### 원인
```python
# CenterModal.on_mount
self._dialog.focus()  # InputModal에 포커스 → Input이 아님
```

### 해결
- `CenterModal.on_mount`에서 **dialog.focus() 제거**
- `InputModal.on_mount`:
  ```python
  self.call_after_refresh(lambda: self.query_one(Input).focus())
  ```

---

## 7. Ubuntu minimal — venv without pip

### 증상
`.venv/bin/activate` 없음, pip 없음.

### 해결
```bash
python3 -m venv --without-pip .venv
.venv/bin/python get-pip.py
pip install -r requirements.txt
```

---

## 8. 모달 체인 (북마크 → 이름 입력)

### 주의
`_pick()` 순서:
```python
def _pick(self, key, value):
    if self._on_pick:
        self._on_pick(key, value)  # 새 모달 마운트 가능
    self._close()  # 이전 모달 제거
```

`restore_panel_after_modal`은 **`CenterModal`이 하나도 없을 때만** 실행:
```python
if app.query("CenterModal"):
    return  # 아직 다음 모달 열려 있음
```

---

## 디버깅 팁

1. **Textual Pilot 테스트**
   ```python
   async with app.run_test(size=(100, 30)) as pilot:
       await pilot.press('b')
       assert app.focused.id == 'left-panel-table'
   ```

2. **포커스 확인:** `active` 클래스와 `app.focused` id가 일치하는지 항상 검증

3. **레이아웃 확인:** `widget.size`가 `0`이 아닌지, overlay가 100% 덮지 않는지
