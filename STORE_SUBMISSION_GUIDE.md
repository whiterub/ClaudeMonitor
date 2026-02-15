# ClaudeMonitor - Microsoft Store 제출 가이드

## 프로젝트 정보
- **앱**: ClaudeMonitor (Claude AI 사용량 모니터 데스크톱 위젯)
- **빌드**: Python 3.12 + Nuitka (MinGW64) → standalone EXE
- **패키징**: 수동 MSIX (Visual Studio 미사용)
- **Publisher**: whiterub
- **Publisher CN**: CN=8E17FE56-1F32-4CB9-894A-6225A3DB2BE1

---

## 1. 빌드 절차

### 1-1. Nuitka로 standalone EXE 빌드
```bat
python -m nuitka --standalone ^
    --windows-console-mode=disable ^
    --enable-plugin=tk-inter ^
    --include-data-dir=assets=assets ^
    --output-filename=ClaudeMonitor.exe ^
    --output-dir=dist ^
    --mingw64 ^
    --windows-icon-from-ico=msix\Assets\icon.ico ^
    --company-name=ClaudeMonitor ^
    --product-name=ClaudeMonitor ^
    --file-version=1.0.3 ^
    --file-description="Claude AI Usage Monitor" ^
    --copyright="MIT License" ^
    main.py
```
- 출력: `dist\main.dist\` 폴더에 standalone 실행 파일들

### 1-2. MSIX 패키지 레이아웃 조립
```
msix_package\
├── ClaudeMonitor.exe  (+ Nuitka 출력물 전체)
├── Assets\
│   ├── StoreLogo.png
│   ├── Square150x150Logo.png
│   ├── Square44x44Logo.png
│   └── (기타 아이콘 PNG)
├── AppxManifest.xml
└── resources.pri
```

### 1-3. resources.pri 생성
```powershell
$SdkBin = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64"
& "$SdkBin\makepri.exe" createconfig /cf priconfig.xml /dq "ko-KR_en-US" /o
& "$SdkBin\makepri.exe" new /pr msix_package /cf priconfig.xml /of msix_package\resources.pri /o
Remove-Item priconfig.xml
```

### 1-4. MakeAppx로 .msix 생성
```powershell
& "$SdkBin\makeappx.exe" pack /d msix_package /p ClaudeMonitor_1.0.3.0_x64.msix /o
```

### 1-5. 서명
- **Store 제출용**: 서명 불필요 (Store가 자체 재서명)
- **사이드로드용**: signtool로 서명 필요
  ```powershell
  & "$SdkBin\signtool.exe" sign /fd SHA256 /a /f ClaudeMonitor-Dev.pfx /p <비밀번호> ClaudeMonitor_1.0.3.0_x64.msix
  ```

---

## 2. AppxManifest.xml (최종 정상 버전)

```xml
<?xml version="1.0" encoding="utf-8"?>
<Package
  xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
  xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
  xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
  xmlns:desktop="http://schemas.microsoft.com/appx/manifest/desktop/windows10">

  <Identity
    Name="whiterub.ClaudeMonitor"
    Publisher="CN=8E17FE56-1F32-4CB9-894A-6225A3DB2BE1"
    Version="1.0.3.0"
    ProcessorArchitecture="x64" />

  <Properties>
    <DisplayName>ClaudeMonitor</DisplayName>
    <PublisherDisplayName>whiterub</PublisherDisplayName>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.19041.0" />
  </Dependencies>

  <Resources>
    <Resource Language="ko-kr" />
    <Resource Language="en-us" />
  </Resources>

  <Applications>
    <Application
      Id="ClaudeMonitor"
      Executable="ClaudeMonitor.exe"
      EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="ClaudeMonitor"
        Description="Claude AI Usage Monitor Widget"
        BackgroundColor="transparent"
        Square150x150Logo="Assets\Square150x150Logo.png"
        Square44x44Logo="Assets\Square44x44Logo.png" />
    </Application>
  </Applications>

  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>

</Package>
```

---

## 3. 매니페스트 삽질 히스토리 & 교훈

### 시도 1: 원본 매니페스트
- `internetClient` capability 포함
- `DefaultTile` (Wide310x150, Square310x310) 포함
- `BackgroundColor="#1e1e2e"`
- `<Description>` Properties에 포함
- **결과**: `.msix` 업로드 자체가 안 됨

### 시도 2: 코파일럿 권장대로 수정
- `Windows.Universal MinVersion="10.0.0.0"` 추가
- `internetClient` 제거
- `DefaultTile` 제거
- `BackgroundColor="transparent"`
- **결과**: ❌ `Windows MinVersion <= 10.0.17134.0을 대상으로 하는 패키지를 업로드할 수 없습니다`
- **원인**: `Windows.Universal MinVersion="10.0.0.0"`이 Store 최소 요구사항(> 10.0.17134.0) 미달

### 시도 3: Windows.Universal 제거
- `Windows.Desktop`만 유지 (`MinVersion="10.0.17763.0"`)
- `Windows.Universal` 완전 제거
- **결과**: ✅ 업로드 성공 (Analyzing package 단계 통과)
- 하지만 인증 단계에서 실패 (보고서 미생성)

### 시도 4: 버전 1.0.3.1로 올리기
- `Version="1.0.3.0"` → `Version="1.0.3.1"`
- **결과**: ❌ `앱은 앱 매니페스트에서 지정한 0이 아닌 수정 번호의 버전을 사용할 수 없습니다`
- **원인**: Store는 4번째 자리(Revision)가 반드시 0이어야 함. 코파일럿이 "Revision만 증가도 괜찮다"고 했지만 **틀림**

### 시도 5: 버전 1.0.4.0으로 올리기
- `Version="1.0.4.0"` (4번째 자리 0 유지)
- **결과**: ✅ 업로드 성공 → 사전 처리 통과 → 인증 실패
- **에러**: `이 제출에 디지털 서명할 수 없습니다`
- Publisher 값 일치 확인 완료, 패키지 미서명 확인 완료, WACK 로컬 WARNING(FAIL 없음)
- **원인 추정**: MS 측 서명 파이프라인 이슈
- **조치**: reportapp@microsoft.com에 문의 메일 발송 + 재제출

### 시도 6: 영어 Store 목록 추가 후 재제출
- 영어(미국) Store 목록 추가 (매니페스트에 en-us 선언되어 있으므로 목록도 필요)
- 재제출 진행 중 → 결과 대기

### 핵심 교훈
| 항목 | 주의사항 |
|---|---|
| **TargetDeviceFamily** | Desktop 풀트러스트 앱은 `Windows.Desktop`만. `Windows.Universal` 추가하면 MinVersion 충돌 위험 |
| **MinVersion** | Store는 `> 10.0.17134.0` 요구. `10.0.17763.0` (Win10 1809) 이상 권장 |
| **internetClient** | fullTrust 앱은 이미 네트워크 권한 포함이므로 불필요. 제거 |
| **DefaultTile** | 필수 아님. 간소화 권장 |
| **BackgroundColor** | `transparent` 권장 |
| **Description (Properties)** | 필수 아님. 제거 가능 |
| **서명** | Store 제출용은 서명 불필요. Store가 재서명. 단, Identity/Publisher가 Partner Center와 정확히 일치해야 함 |
| **버전 Revision** | 4번째 자리는 **반드시 0**. `1.0.3.1` ❌ → `1.0.4.0` ✅. Store가 Revision을 내부적으로 관리 |
| **버전 올리기** | 같은 버전 재업로드 불가. 3번째 자리(Build) 이상을 올려야 함 |

---

## 4. Partner Center 업로드 방법

### 업로드 파일 형식
- **권장**: `.msix` 직접 업로드 (PDB 없으므로 `.msixupload` 불필요)
- `.msixupload`는 `.msix` + `.appxsym`(PDB 심볼)을 zip으로 묶은 것
- Nuitka/MinGW 빌드는 PDB를 생성하지 않으므로 `.msixupload` 만들 필요 없음
- **주의**: `.msix`와 `.msixupload`를 동시에 올리면 이름 충돌 에러 발생

### 업로드 시 에러 대응
| 에러 | 원인 | 해결 |
|---|---|---|
| `Windows MinVersion <= 10.0.17134.0` | Windows.Universal MinVersion 너무 낮음 | Windows.Universal 제거 또는 MinVersion 올리기 |
| `전체 이름 기준으로 고유하게 식별되어야 합니다` | 같은 이름의 .msix와 .msixupload 동시 존재 | 하나 삭제 (Delete 클릭) |
| `runFullTrust 경고` | ⚠️ 경고일 뿐 에러 아님 | Notes for certification에 사유 기재 |
| `0이 아닌 수정 번호의 버전` | Version 4번째 자리가 0이 아님 | `X.X.X.0` 형식으로 수정 (Revision은 항상 0) |
| `인증 실패 - 보고서 미생성` | 원인 불명 (매니페스트/패키지 외 문제) | 버전 올려서 재제출 or reportapp@microsoft.com 문의 |

### Notes for certification 기재 내용
```
Desktop(full-trust) 위젯 앱이며 시스템 트레이/오버레이 위젯 구현을 위해 runFullTrust 필요.
앱 실행/재현: 설치 후 시작 메뉴에서 'ClaudeMonitor' 실행 → 트레이 아이콘/위젯 표시 확인.
```

---

## 5. 버전 올릴 때 체크리스트

1. `version.py`에서 버전 변경
2. `msix\AppxManifest.xml`의 `<Identity Version="X.X.X.0" />` 변경
3. Nuitka 빌드: `build_standalone.bat` 실행
4. `msix_package\`에 빌드 출력물 + Assets + AppxManifest.xml 복사
5. `makepri`로 `resources.pri` 재생성
6. `makeappx pack`으로 `.msix` 생성
7. Partner Center에 `.msix` 업로드
8. 이전 패키지가 있으면 **Delete** 후 새 패키지만 유지

---

## 6. SDK 도구 경로
```
signtool: C:\Program Files (x86)\Windows Kits\10\bin\10.0.18362.0\x64\signtool.exe
makeappx: C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\makeappx.exe
makepri:  C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\makepri.exe
```

---

## 7. 참고 사항
- Store 재서명 전제조건: `Identity`의 `Name`과 `Publisher`가 Partner Center의 Product Identity와 **문자 단위로 동일**
- WACK(Windows App Certification Kit)로 사전 검증 권장
- `.msixupload`는 나중에 PDB 심볼이 필요할 때 만들면 됨 (크래시 분석용)
- `build_msix.ps1` 스크립트로 전체 빌드 자동화 가능
