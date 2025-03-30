@echo off
echo ===== Construint l'executable de MultiTerminal =====

REM Netegem carpetes anteriors
echo Netejant carpetes anteriors...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Executem PyInstaller amb l'especificació
echo Executant PyInstaller...
pyinstaller multiterminal.spec

if errorlevel 1 (
    echo Error durant la construcció!
    pause
    exit /b 1
)

echo Construcció completada amb èxit!
echo L'executable està a: dist\MultiTerminal\MultiTerminal.exe

REM Copia un layout per defecte a la carpeta de l'executable
echo Copiant layout per defecte...
if not exist dist\MultiTerminal\layouts mkdir dist\MultiTerminal\layouts
copy esunaprova.json dist\MultiTerminal\layouts\default_layout.json

echo Ara pots distribuir la carpeta dist\MultiTerminal
pause