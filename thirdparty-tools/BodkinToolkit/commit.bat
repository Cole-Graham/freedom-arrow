@echo off
echo ========================================
echo          Git Auto-Commit Script
echo ========================================
echo.
git status
echo.
set /p commit_msg="Enter your new commit message: "
echo.
echo Staging files...
git add .
echo Committing changes...
git commit -m "%commit_msg%"
echo.
echo Done!
pause