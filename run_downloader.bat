@echo off
echo Country Image Downloader
echo ----------------------
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking requirements...
pip show selenium >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing requirements...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error installing requirements.
        pause
        exit /b 1
    )
)

echo.
echo Starting the downloader...
echo.

REM Run the script
python country_image_downloader.py %*

echo.
if %errorlevel% neq 0 (
    echo An error occurred while running the script.
) else (
    echo Download completed successfully!
)

pause