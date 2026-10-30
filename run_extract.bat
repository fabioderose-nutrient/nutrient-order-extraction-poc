@echo off
setlocal
call "%~dp0venv\Scripts\activate.bat"
python "%~dp0extract_order.py" %*
set EXITCODE=%ERRORLEVEL%
endlocal & exit /b %EXITCODE%
