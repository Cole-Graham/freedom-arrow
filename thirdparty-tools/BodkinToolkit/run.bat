@echo off
setlocal enableextensions
chcp 65001 >nul
cd /d "%~dp0"

rem --- toolkit folder name must be a valid Python package identifier ---
for %%I in ("%~dp0.") do set "NAME=%%~nxI"
echo %NAME%| findstr /R /C:"^[A-Za-z_][A-Za-z0-9_]*$" >nul
if errorlevel 1 (
  echo.
  echo  ====================================================================
  echo   WARNING: toolkit folder name "%NAME%" is not a valid Python name.
  echo   Use only letters, digits and underscore - no spaces or hyphens
  echo   ^(e.g. "Bodkin"^). The toolkit cannot import its packages otherwise.
  echo  ====================================================================
  echo.
  pause
  exit /b 1
)

rem --- locate Python ---
set "PY=python"
where %PY% >nul 2>nul || set "PY=py"
where %PY% >nul 2>nul || (
  echo.
  echo  WARNING: Python not found on PATH. Install Python 3 then retry.
  echo.
  pause
  exit /b 1
)

rem --- first run: vendor dependencies for THIS platform (Windows wheels) ---
if not exist "%~dp0vendor\UnityPy" (
  echo  First run: installing dependencies into vendor\ ...
  %PY% -m pip install -r "%~dp0requirements.txt" -t "%~dp0vendor"
  if errorlevel 1 (
    echo.
    echo  WARNING: dependency install failed. Check pip and network, then retry:
    echo    %PY% -m pip install -r requirements.txt -t vendor
    echo.
    pause
    exit /b 1
  )
)

rem --- launch the menu ---
%PY% "%~dp0menu\menu.py" %*
if errorlevel 1 (
  echo.
  echo  Menu exited with an error ^(code %ERRORLEVEL%^).
  pause
)
endlocal
exit /b %ERRORLEVEL%
