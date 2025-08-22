@echo off

REM Check if Python 3 is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3 not found. Installation starts...
    echo Please install Python 3 from https://www.python.org/downloads/ and ensure it's in your PATH.
    goto end
) else (
    echo Python 3 is already installed.
)

REM Set path variables
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%\.venv

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
set VENV_PIP="%VENV_DIR%\Scripts\pip.exe"

REM Install the project and its dependencies from pyproject.toml
echo Installing the project and its dependencies from pyproject.toml...

REM Install the project in editable mode, including dev and test dependencies
%VENV_PIP% install -e ".[dev,test]"

REM Show all installed libraries
echo Following libraries are now available in the virtual environment:
%VENV_PIP% list

:end
