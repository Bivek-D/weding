@echo off
rem Runs your Blender (D:\blender.exe) with every config, cache and temp file kept inside the project.
rem Usage: blender.cmd [blender args]   e.g.  blender.cmd -b -P render_pandal.py -- --part altar
setlocal
if not defined BLENDER set "BLENDER=D:\blender.exe"
set "C=%~dp0..\..\..\.cache"
for %%d in (blender-user tmp appdata) do if not exist "%C%\%%d" mkdir "%C%\%%d"
set "BLENDER_USER_RESOURCES=%C%\blender-user"
set "TEMP=%C%\tmp"
set "TMP=%C%\tmp"
set "APPDATA=%C%\appdata"
set "LOCALAPPDATA=%C%\appdata"
cd /d "%~dp0"
"%BLENDER%" --factory-startup %*
