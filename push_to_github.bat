@echo off
echo ========================================
echo   Pushing CDR Analysis Pro to GitHub
echo ========================================
echo.

REM Set Git path
set GIT="C:\Program Files\Git\cmd\git.exe"

REM Configure Git user
echo Configuring Git user...
%GIT% config --global user.name "Sneha-Suresh-git"
%GIT% config --global user.email "snehasuresh11102004@gmail.com"

REM Check if already initialized
if not exist .git (
    echo Initializing Git repository...
    %GIT% init
)

REM Add all files
echo Adding files...
%GIT% add .

REM Commit
echo Committing files...
%GIT% commit -m "Initial commit: CDR Analysis Pro with tower location and bill analysis"

REM Rename branch to main
echo Renaming branch to main...
%GIT% branch -M main

REM Add remote (ignore error if already exists)
echo Adding remote repository...
%GIT% remote add origin https://github.com/Sneha-Suresh-git/CDR-sneha.git 2>nul

REM Push to GitHub
echo.
echo Pushing to GitHub...
echo You may be prompted for your GitHub credentials.
echo.
%GIT% push -u origin main

echo.
echo ========================================
echo   Done! Check: https://github.com/Sneha-Suresh-git/CDR-sneha
echo ========================================
pause
