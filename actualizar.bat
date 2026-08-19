@echo off
REM ===========================================================================
REM  Rehace esta carpeta a partir de app\ para volver a publicar.
REM  Doble clic y listo. Solo copia: no borra nada.
REM
REM  IMPORTANTE antes de subir a GitHub: si cambiaste la app, sube el numero
REM  de version en app\sw.js  ->  const CACHE = "tk-termostato-v4"  ->  v5
REM  Si no, los telefonos que ya la instalaron siguen viendo la version vieja.
REM ===========================================================================

setlocal
set ORIGEN=%~dp0..\app

echo Copiando desde %ORIGEN%
echo.

copy /Y "%ORIGEN%\termostato-1-rele.html"        "%~dp0" >nul
copy /Y "%ORIGEN%\termostato-1-rele.webmanifest" "%~dp0" >nul
copy /Y "%ORIGEN%\sw.js"                         "%~dp0" >nul
copy /Y "%ORIGEN%\icono-app-oscuro.svg"          "%~dp0" >nul
copy /Y "%ORIGEN%\icono-app-redondeado.svg"      "%~dp0" >nul

echo Carpeta lista. Sube TODO lo que hay aqui a GitHub.
echo.
findstr /C:"const CACHE" "%~dp0sw.js"
echo.
echo Si cambiaste la app y ese numero es el mismo de la ultima vez, subelo.
echo.
pause
