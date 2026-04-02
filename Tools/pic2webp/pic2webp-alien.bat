@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=C:\Program Files\Python314\python.exe"

if exist "%PYTHON_EXE%" (
  "%PYTHON_EXE%" "%SCRIPT_DIR%pic2webp-alien.py" %*
) else (
  py -3 "%SCRIPT_DIR%pic2webp-alien.py" %*
)

endlocal