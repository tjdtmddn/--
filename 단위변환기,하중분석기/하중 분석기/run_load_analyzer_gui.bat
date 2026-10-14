@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "GUI_SCRIPT=%~dp0load_analyzer_gui.py"

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

"%PYTHON_EXE%" "%GUI_SCRIPT%"
if errorlevel 1 (
    echo.
    echo The GUI could not be started.
    pause
)

endlocal
