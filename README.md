# ClaudeMonitor

Claude AI 사용량을 실시간으로 보여주는 Windows 데스크톱 위젯입니다.

![ClaudeMonitor](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## 주요 기능

- **실시간 사용량 모니터링** - 5시간 세션, 주간 전체, Sonnet 주간 사용량을 한눈에
- **항상 위에 표시** - 프레임 없는 투명 위젯으로 작업 방해 없이 사용량 확인
- **시스템 트레이** - 트레이 아이콘으로 표시/숨기기, 새로고침, 설정 접근
- **인앱 OAuth 로그인** - 터미널 없이 브라우저로 바로 Claude 로그인
- **맞춤 설정** - 위젯 크기 (소/중/대), 투명도, 갱신 주기, 표시 항목 선택
- **드래그 이동** - 원하는 위치에 위젯 배치

## 스크린샷

```
┌──────────────────┐
│ ClaudeMonitor  ⚙✕│
│ ☑ 5H  ██████ 45% │
│     2시간 32분 후 │
│ ☑ 7D  ████── 60% │
│     3일 후 리셋   │
│ ☑ Son ██──── 30% │
│     3일 후 리셋   │
│ ● 12:34 갱신  ↻  │
└──────────────────┘
```

## 설치 및 실행

### 방법 1: EXE 파일 (권장)

1. [Releases](https://github.com/whiterub/ClaudeMonitor/releases) 페이지에서 `ClaudeMonitor.exe` 다운로드
2. 실행 후 설정(⚙) → `Claude 로그인` 클릭
3. 브라우저에서 Claude 계정으로 인증

### 방법 2: Python으로 직접 실행

```bash
# 저장소 클론
git clone https://github.com/whiterub/ClaudeMonitor.git
cd ClaudeMonitor

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

## 사용법

### 첫 실행
1. 위젯 상단의 ⚙ 버튼 또는 우클릭 → 설정
2. `Claude 로그인` 버튼 클릭
3. 브라우저에서 Claude 계정으로 로그인
4. 인증 완료 후 자동으로 사용량 표시

### 위젯 조작
| 동작 | 설명 |
|------|------|
| 드래그 | 위젯 위치 이동 |
| 우클릭 | 컨텍스트 메뉴 (새로고침, 설정, 후원, 종료) |
| ⚙ 버튼 | 설정 열기 |
| ✕ 버튼 | 트레이로 숨기기 |
| 체크박스 | 표시 항목 토글 |
| ↻ 버튼 | 수동 새로고침 |

### 설정 항목
- **표시 항목**: 5시간 세션 / 주간 전체 / Sonnet 주간
- **위젯 크기**: 소 / 중 / 대
- **갱신 주기**: 5~300초 (기본 30초)
- **투명도**: 0.3~1.0 (기본 0.9)

## 빌드

```bash
# PyInstaller로 EXE 빌드
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "assets;assets" --name ClaudeMonitor --icon assets/icon.ico main.py
```

또는 `build.bat` 실행

## 기술 스택

- **Python 3.10+**
- **CustomTkinter** - 모던 UI
- **pystray** - 시스템 트레이
- **Pillow** - 이미지 처리
- **OAuth 2.0 + PKCE** - Claude AI 인증

## 파일 구조

```
ClaudeMonitor/
├── main.py            # 엔트리 포인트
├── widget.py          # 메인 위젯 UI
├── config.py          # 설정 관리
├── api_client.py      # OAuth + API 클라이언트
├── setup_dialog.py    # 설정/후원 다이얼로그
├── tray.py            # 시스템 트레이
├── utils.py           # 유틸리티 함수
├── build.bat          # 빌드 스크립트
├── requirements.txt   # Python 의존성
└── assets/
    └── donate_qr.png  # 후원 QR
```

## 후원

커피 한 잔 후원은 큰 힘이 됩니다!
위젯 우클릭 → "후원하기" 에서 카카오페이 QR을 확인하세요.

## License

MIT License
