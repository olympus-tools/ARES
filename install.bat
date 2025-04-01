@echo off

REM Check if Python 3 is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3 not found. Installation starts...
    REM Note: Windows does not have a built-in package manager like apt. You'll need to install Python manually.
    echo Please install Python 3 and ensure it's in your PATH.
    goto end
) else (
    echo Python 3 is already installed.
)

REM Check if venv is available
python -m venv --help >nul 2>&1
if %errorlevel% neq 0 (
    echo python3-venv not found. Installation starts...
    REM Note: venv is usually part of Python 3 installation, but might need to be enabled.
    echo Please ensure the venv module is available in your Python 3 installation.
    goto end
) else (
    echo python3-venv is already installed.
)

REM Set path variables
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%\venv_win

REM Check if the virtual environment exists, delete it and recreate it if it does.
if exist "%VENV_DIR%" (
    echo Virtual environment already exists. Cleaning it up...
    rmdir /s /q "%VENV_DIR%"
    echo Creating new virtual environment in %VENV_DIR%...
    python -m venv "%VENV_DIR%"
) else (
    echo Creating virtual environment in %VENV_DIR%...
    python -m venv "%VENV_DIR%"
)
 
REM Use the absolute path to pip in the virtual environment
set VENV_PIP=%VENV_DIR%\Scripts\pip.exe

REM Install the project and its dependencies via setup.py
echo Installing the project and its dependencies using setup.py...
"%VENV_PIP%" install .

REM Show all installed libraries
echo Following libraries are now available in the virtual environment:
"%VENV_PIP%" list

:end