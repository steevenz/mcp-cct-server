@echo off
REM CMD Wrapper for CCT Artisan Setup System
REM Author: Steeven Andrian

pushd %~dp0\..\..
powershell -ExecutionPolicy Bypass -File .bin\setup.ps1 %*
popd
