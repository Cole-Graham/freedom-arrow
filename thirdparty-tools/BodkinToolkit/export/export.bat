@echo off
rem export — Windows proxy for manual access. Forwards all args to export.py.
python "%~dp0export.py" %*
