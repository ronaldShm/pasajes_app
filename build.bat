@echo off
echo ========================================
echo  Construyendo ejecutable para Windows...
echo ========================================

pyinstaller --onefile --windowed --name "GestorPasajes" --clean main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  ¡Ejecutable creado exitosamente!
    echo  Ubicacion: dist\GestorPasajes.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo  Error al crear el ejecutable
    echo ========================================
)

pause
