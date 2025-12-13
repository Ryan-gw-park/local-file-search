@echo off
chcp 65001
cls

echo ========================================================
echo  Local AI File Search - 자동 빌드 도구
echo ========================================================
echo.

:: 1. Check Python
echo [1/4] Python 설치 확인 중...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo 1. https://www.python.org/downloads/ 에 접속하세요.
    echo 2. Python을 다운로드하고 설치하세요.
    echo 3. 설치 화면 맨 아래의 "Add Python to PATH" 체크박스를 꼭! 체크해주세요.
    echo.
    echo 설치 후 이 파일을 다시 실행해주세요.
    pause
    exit /b
)
echo Python이 정상적으로 설치되어 있습니다:
python --version
echo.

:: 2. Install Dependencies
echo [2/4] 필요한 프로그램 설치 중... (인터넷 연결 필요)
echo 잠시만 기다려주세요...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [오류] pip 업데이트 실패. 인터넷 연결을 확인해주세요.
    pause
    exit /b
)

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [오류] 필수 라이브러리 설치 실패.
    echo 위 에러 메시지를 확인해주세요. (C++ Build Tools 등 필요)
    pause
    exit /b
)

python -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo [오류] PyInstaller 설치 실패.
    pause
    exit /b
)
echo 설치 완료.
echo.

:: 3. Build Selection
echo [3/4] 빌드할 버전을 선택하세요.
echo 1. 한국어 버전 (성능 좋음, 용량 큼) - 추천
echo 2. 영어 버전 (빠름, 용량 작음)
echo.
set /p choice="번호를 입력하고 엔터를 누르세요 (1 또는 2): "

echo.
echo 실행 파일을 만드는 중입니다... (약 1~3분 소요)

if "%choice%"=="1" (
    python -m PyInstaller build_kr.spec
) else (
    python -m PyInstaller build_en.spec
)

if %errorlevel% neq 0 (
    echo.
    echo [오류] 빌드 중 에러가 발생했습니다!
    echo 위 로그 내용을 확인해주세요.
    pause
    exit /b
)

:: 4. Finish
echo.
echo ========================================================
echo [4/4] 모든 작업이 완료되었습니다!
echo.
if exist "dist\*.exe" (
    echo 'dist' 폴더를 열어보세요. 실행 파일이 들어있습니다.
) else (
    echo [주의] dist 폴더에 실행 파일이 보이지 않습니다. 빌드 로그를 확인하세요.
)
echo ========================================================
pause
