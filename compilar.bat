@echo off
rem Compila todo el proyecto en tres pasos:
rem   1. flex lee analizador.l y genera lex.yy.c
rem   2. gcc compila lex.yy.c y genera analizador.exe
rem   3. pyinstaller junta app.py, sintactico.py, semantico.py y analizador.exe en AnalizadorSemantico.exe
rem Si flex y gcc estan en otra carpeta, cambiar HERRAMIENTAS.

cd /d "%~dp0"
set HERRAMIENTAS=%USERPROFILE%\herramientas-compiladores

echo [1/3] flex: analizador.l a lex.yy.c
"%HERRAMIENTAS%\flex\win_flex.exe" -o lex.yy.c analizador.l
if errorlevel 1 goto error

echo [2/3] gcc: lex.yy.c a analizador.exe
"%HERRAMIENTAS%\mingw64\bin\gcc.exe" -o analizador.exe lex.yy.c
if errorlevel 1 goto error

rem si la app esta abierta no se puede reemplazar el .exe, asi que se cierra
taskkill /im AnalizadorSemantico.exe /f >nul 2>&1

echo [3/3] pyinstaller: app.py a AnalizadorSemantico.exe (tarda como un minuto)
python -m PyInstaller --noconfirm --log-level WARN --onefile --windowed --name AnalizadorSemantico --add-binary "%~dp0analizador.exe;." --distpath . --workpath build --specpath build app.py
if errorlevel 1 goto error

echo.
echo Listo, se genero AnalizadorSemantico.exe
start "" AnalizadorSemantico.exe
goto fin

:error
echo.
echo Hubo un error al compilar.

:fin
pause
