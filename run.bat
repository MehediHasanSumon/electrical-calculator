@echo off
setlocal EnableExtensions

rem ================================================================
rem  Electrical Calculator - Windows launcher
rem ================================================================

title Electrical Calculator
color 0B
chcp 65001 >nul 2>&1

rem Always work from the folder containing this batch file.
cd /d "%~dp0"

set "VENV_DIR=%~dp0venv"
set "SYSTEM_PYTHON="

call :banner

echo Checking application files...
if not exist "%~dp0main.py" goto :main_missing
echo [OK] main.py found.
echo.

call :check_python
if errorlevel 1 goto :python_missing

call :setup_venv
set "STAGE_EXIT_CODE=%errorlevel%"
if "%STAGE_EXIT_CODE%"=="2" goto :cancelled
if not "%STAGE_EXIT_CODE%"=="0" goto :venv_error

call :activate_venv
if errorlevel 1 goto :activation_error

call :install
set "STAGE_EXIT_CODE=%errorlevel%"
if "%STAGE_EXIT_CODE%"=="2" goto :cancelled
if not "%STAGE_EXIT_CODE%"=="0" goto :install_error

goto :run


:banner
echo =======================================================
echo              ELECTRICAL CALCULATOR
echo =======================================================
echo.
exit /b 0


:check_python
echo Checking Python...

rem Prefer the official Windows Python launcher when available.
where py >nul 2>&1
if errorlevel 1 goto :check_python_command

py -3 --version >nul 2>&1
if errorlevel 1 goto :check_python_command

set "SYSTEM_PYTHON=py -3"
for /f "tokens=*" %%V in ('py -3 --version 2^>^&1') do echo [OK] %%V
echo.
exit /b 0


:check_python_command
where python >nul 2>&1
if errorlevel 1 exit /b 1

python --version >nul 2>&1
if errorlevel 1 exit /b 1

python -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)" >nul 2>&1
if errorlevel 1 exit /b 1

set "SYSTEM_PYTHON=python"
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo [OK] %%V
echo.
exit /b 0


:setup_venv
echo Checking Virtual Environment...

if exist "%VENV_DIR%\Scripts\python.exe" (
    echo [OK] Virtual environment is ready.
    echo.
    exit /b 0
)

echo Creating virtual environment...
%SYSTEM_PYTHON% -m venv "%VENV_DIR%"
set "SETUP_EXIT_CODE=%errorlevel%"

if "%SETUP_EXIT_CODE%"=="-1073741510" exit /b 2
if "%SETUP_EXIT_CODE%"=="3221225786" exit /b 2
if not "%SETUP_EXIT_CODE%"=="0" exit /b %SETUP_EXIT_CODE%

if not exist "%VENV_DIR%\Scripts\python.exe" exit /b 1

echo [OK] Virtual environment created.
echo.
exit /b 0


:activate_venv
echo Activating Virtual Environment...

if not exist "%VENV_DIR%\Scripts\activate.bat" exit /b 1

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 exit /b 1

echo [OK] Virtual environment activated.
echo.
exit /b 0


:install
echo Upgrading pip...
python -m pip install --upgrade pip
set "PIP_EXIT_CODE=%errorlevel%"

if "%PIP_EXIT_CODE%"=="-1073741510" exit /b 2
if "%PIP_EXIT_CODE%"=="3221225786" exit /b 2
if not "%PIP_EXIT_CODE%"=="0" exit /b %PIP_EXIT_CODE%

if not exist "%~dp0requirements.txt" (
    echo.
    echo [WARNING] requirements.txt was not found.
    echo [WARNING] Dependency installation will be skipped.
    echo.
    exit /b 0
)

echo.
echo Installing Dependencies...
python -m pip install -r "%~dp0requirements.txt"
set "INSTALL_EXIT_CODE=%errorlevel%"

if "%INSTALL_EXIT_CODE%"=="-1073741510" exit /b 2
if "%INSTALL_EXIT_CODE%"=="3221225786" exit /b 2
if not "%INSTALL_EXIT_CODE%"=="0" exit /b %INSTALL_EXIT_CODE%

echo [OK] Dependencies are ready.
echo.
exit /b 0


:run
echo Starting Application...
echo.
echo =======================================================
echo.

python main.py
set "APP_EXIT_CODE=%errorlevel%"

if "%APP_EXIT_CODE%"=="-1073741510" goto :cancelled
if "%APP_EXIT_CODE%"=="3221225786" goto :cancelled
if "%APP_EXIT_CODE%"=="0" goto :normal_exit

color 0C
echo.
echo Error:
echo The application exited with error code %APP_EXIT_CODE%.
echo Review the messages above for more information.
echo.
echo Press any key to exit...
pause >nul
exit /b %APP_EXIT_CODE%


:normal_exit
endlocal
exit /b 0


:cancelled
color 07
echo.
echo Operation cancelled. Exiting gracefully...
timeout /t 1 /nobreak >nul 2>&1
endlocal
exit /b 0


:main_missing
color 0C
echo.
echo Error:
echo main.py was not found.
echo.
echo Press any key to exit...
pause >nul
endlocal
exit /b 1


:python_missing
color 0C
echo.
echo Error:
echo Python 3 was not found.
echo Install Python 3 and enable "Add Python to PATH", then try again.
echo.
echo Press any key to exit...
pause >nul
endlocal
exit /b 1


:venv_error
color 0C
echo.
echo Error:
echo The virtual environment could not be created.
echo Check the messages above and verify that Python includes the venv module.
echo.
echo Press any key to exit...
pause >nul
endlocal
exit /b 1


:activation_error
color 0C
echo.
echo Error:
echo The virtual environment could not be activated.
echo Delete the venv folder and run this launcher again.
echo.
echo Press any key to exit...
pause >nul
endlocal
exit /b 1


:install_error
color 0C
echo.
echo Error:
echo Required Python packages could not be installed.
echo Check your internet connection and the messages above.
echo.
echo Press any key to exit...
pause >nul
endlocal
exit /b 1
