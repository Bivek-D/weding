@echo off
rem Runs the dev server with every cache kept inside the project folder (nothing written to C:).
set "ROOT=%~dp0..\..\.cache"
if not exist "%ROOT%\appdata" mkdir "%ROOT%\appdata"
set NEXT_TELEMETRY_DISABLED=1
set "APPDATA=%ROOT%\appdata"
set "LOCALAPPDATA=%ROOT%\appdata"
set "npm_config_cache=%ROOT%\npm"
cd /d "%~dp0"
npm run dev -- %*
