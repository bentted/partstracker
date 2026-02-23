@echo off
title Parts Tracker Application

echo Starting Parts Tracker...
echo.

REM Try to run the fixed version first
if exist "parts_tracker.py" (
    echo Running parts_tracker.py...
    python parts_tracker.py
) else if exist "pparts tracker.py" (
    echo Running pparts tracker.py...
    python "pparts tracker.py"
) else (
    echo ERROR: No Parts Tracker Python file found!
    echo.
    echo Please make sure one of these files exists:
    echo - parts_tracker.py
    echo - pparts tracker.py
    echo.
    pause
    exit /b 1
)

echo.
echo Application has closed.
if errorlevel 1 (
    echo The application may have encountered an error.
    echo Check the output above for details.
)

echo.
pause