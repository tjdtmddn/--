@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "APP_SCRIPT=%~dp0force_converter.py"

if not exist "%PYTHON_EXE%" (
    echo Python environment not found:
    echo %PYTHON_EXE%
    echo.
    echo Create it from the project folder with:
    echo py -m venv "%PROJECT_DIR%\.venv"
    echo "%PROJECT_DIR%\.venv\Scripts\python.exe" -m pip install -r "%PROJECT_DIR%\requirements.txt"
    pause
    exit /b 1
)

"%PYTHON_EXE%" "%APP_SCRIPT%"
if errorlevel 1 (
    echo.
    echo The unit converter could not be started.
    pause
)

endlocal
