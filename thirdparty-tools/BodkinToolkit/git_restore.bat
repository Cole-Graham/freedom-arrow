@echo off
setlocal

cd /d "%~dp0"

echo ======================================================================
echo  Git Restore -- discard all uncommitted changes
echo ======================================================================
echo.

:: Show what will be dropped
git status --short
echo.

:: Count changes so we can bail early if there's nothing to do
for /f %%i in ('git status --porcelain ^| find /c /v ""') do set CHANGES=%%i
if "%CHANGES%"=="0" (
    echo   Nothing to restore -- working tree is already clean.
    goto :done
)

set /p CONFIRM="  Discard ALL uncommitted changes? This cannot be undone. [y/N]: "
if /i not "%CONFIRM%"=="y" (
    echo   Aborted.
    goto :done
)

echo.
echo   Restoring tracked files...
git restore .

echo   Removing untracked files and directories...
git clean -fd

echo.
echo   Done. Working tree restored to last commit.

:done
echo.
pause
endlocal
