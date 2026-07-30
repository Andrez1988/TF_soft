@echo off
title Cronograma Gantt TI - Farmacias Peruanas
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python server.py
    goto :fin
)

where py >nul 2>nul
if %errorlevel%==0 (
    py server.py
    goto :fin
)

echo.
echo No se encontro Python instalado en este equipo.
echo Descargalo desde https://www.python.org/downloads/
echo IMPORTANTE: durante la instalacion, marca la casilla "Add Python to PATH".
echo Luego vuelve a hacer doble clic en este archivo.
echo.
pause
exit /b 1

:fin
echo.
echo El servidor se detuvo.
pause
