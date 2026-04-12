@echo off
REM CMD Wrapper for CCT Setup System
REM Author: Steeven Andrian

pushd %~dp0\..\..
powershell -ExecutionPolicy Bypass -File src\.bin\setup.ps1
popd
pause
