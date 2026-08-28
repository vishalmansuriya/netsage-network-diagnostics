@echo off
setlocal enabledelayedexpansion

:: Change working directory to the project root (ciscovip)
cd /d "%~dp0.."

cls
echo ================================================================================
echo NETSAGE AI - APPLIED AI NETWORK TROUBLESHOOTING DEMO LAUNCHER
echo Cisco Internship Project 2
echo Working Directory: %CD%
echo ================================================================================
echo.

echo [1/4] Running Deterministic Rule Checker Engine...
python checker\rule_checker.py --all --save-sample
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed running rule_checker.py. Make sure Python is in PATH.
)
echo.

echo [2/4] Executing AI Diagnostic Pipeline...
python pipeline\run_diagnosis.py --simulate
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed running run_diagnosis.py.
)
echo.

echo [3/4] Aggregating Analytics and Generating Metrics...
python dashboard\dashboard.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed running dashboard.py.
)
echo.

echo [4/4] Launching Interactive NetSage AI Dashboard in default browser...
start "" "%CD%\dashboard\index.html"
echo.

echo ================================================================================
echo NetSage AI Demo Successfully Launched!
echo Check your web browser for the interactive dashboard.
echo ================================================================================
echo.
pause
