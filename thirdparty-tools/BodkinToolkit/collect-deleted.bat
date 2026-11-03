@echo off
setlocal enabledelayedexpansion

set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"
set "DEST=%BASE%\delete"
if not exist "%DEST%" mkdir "%DEST%"

rem Files
for /r "%BASE%" %%F in (*.delete) do (
    set "FULL=%%F"
    set "REL=!FULL:%BASE%\=!"
    set "REL=!REL:\=-!"
    set "REL=!REL: =-!"
    move "%%F" "%DEST%\!REL!"
)

rem Folders
for /r "%BASE%" %%D in (.) do (
    for /d %%F in ("%%D\*.delete") do (
        set "FULL=%%F"
        set "REL=!FULL:%BASE%\=!"
        set "REL=!REL:\=-!"
        set "REL=!REL: =-!"
        move "%%F" "%DEST%\!REL!"
    )
)