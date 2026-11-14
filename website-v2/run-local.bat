@echo off
rem Field Shift: start the dashboard on Windows. Double-click this file.
setlocal
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" (
  echo First run: creating the Python environment...
  python -m venv .venv || goto :nopython
  ".venv\Scripts\python.exe" -m pip install -q -r requirements.lock.txt || goto :failed
)
echo.
echo Field Shift is starting. Keep this window open while you use the site.
echo Dashboard:  http://127.0.0.1:8000
echo Story page: http://127.0.0.1:8000/story.html
echo.
start "" "http://127.0.0.1:8000"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
goto :eof
:nopython
echo Python was not found. Install Python 3.11 or newer from python.org, then run this file again.
pause
goto :eof
:failed
echo Installing the requirements failed. Check the internet connection and run this file again.
pause
