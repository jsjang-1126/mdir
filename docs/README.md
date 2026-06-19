# mdir 문서

이 폴더는 **mdir** 프로젝트의 전체 개발 과정, 기술 구조, 배포 방법, 그리고 AI와 협업할 때의 요구 방식을 기록합니다.

다른 AI나 개발자가 이 문서만 읽고 **동일한 프로그램을 재구현**하거나, 사용자가 **비슷한 TUI 프로그램을 같은 스타일로 의뢰**할 수 있도록 작성되었습니다.

## 문서 목록

| 문서 | 내용 |
|------|------|
| [01-development-history.md](01-development-history.md) | 사용자 요구 → AI 작업 → 결과 (대화 타임라인) |
| [02-architecture.md](02-architecture.md) | 기술 스택, 파일 구조, 클래스 설계, 데이터 흐름 |
| [03-features-and-keybindings.md](03-features-and-keybindings.md) | 기능 목록, 단축키, 북마크·에디터·상태바 동작 |
| [04-bugs-and-fixes.md](04-bugs-and-fixes.md) | 발생한 버그와 해결 방법 (Textual TUI 패턴) |
| [05-install-and-deploy.md](05-install-and-deploy.md) | 로컬 설치, PATH, iwin 원격 서버 배포 |
| [06-ai-collaboration-guide.md](06-ai-collaboration-guide.md) | 앞으로 비슷한 프로그램을 의뢰할 때의 가이드 |

## 프로젝트 한 줄 요약

**mdir** = Ubuntu/Linux 터미널용 **2패널 텍스트 파일 탐색기** (Midnight Commander 스타일). Python **Textual** 프레임워크로 구현.

## 빠른 실행

```bash
mdir
mdir ~/Downloads
```

설치·배포 상세는 [05-install-and-deploy.md](05-install-and-deploy.md) 참고.
