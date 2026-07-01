@echo off
chcp 65001 >nul 2>&1
setlocal EnableExtensions

set "ROOT=%~dp0"
set "FRONTEND_PORT=3000"
set "BACKEND_PORT=8000"
cd /d "%ROOT%"

echo ========================================
echo   TIP - Trello Intelligence Platform
echo ========================================
echo.

where docker >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [1/5] Iniciando PostgreSQL e Redis ^(Docker^)...
    docker compose up -d
    if %ERRORLEVEL% neq 0 (
        echo       AVISO: Falha ao subir containers. Verifique se o Docker Desktop esta ativo.
    ) else (
        echo       Aguardando banco de dados...
        timeout /t 5 /nobreak >nul
    )
) else (
    echo [1/5] Docker nao encontrado — PostgreSQL deve estar em localhost:5433
)

if not exist "%ROOT%.venv\Scripts\python.exe" (
    echo.
    echo ERRO: Ambiente virtual nao encontrado em .venv
    echo Crie com: python -m venv .venv
    echo Depois:    .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [2/5] Liberando portas %BACKEND_PORT% e %FRONTEND_PORT%...
call :KillPort %BACKEND_PORT%
call :KillPort %FRONTEND_PORT%
timeout /t 2 /nobreak >nul

echo [3/5] Iniciando backend Django ^(http://127.0.0.1:%BACKEND_PORT%^)...
start "TIP Backend" cmd /k "cd /d "%CD%" && .venv\Scripts\python.exe manage.py runserver %BACKEND_PORT%"

if not exist "%ROOT%frontend\node_modules\" (
    echo       Instalando dependencias do frontend ^(primeira vez^)...
    pushd "%ROOT%frontend"
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo ERRO: npm install falhou. Verifique se o Node.js esta instalado.
        popd
        pause
        exit /b 1
    )
    popd
)

echo [4/5] Iniciando frontend Next.js ^(http://localhost:%FRONTEND_PORT%^)...
start "TIP Frontend" cmd /k "cd /d "%CD%\frontend" && npm run dev:3000"

echo [5/5] Aguardando frontend responder ^(ate 60s^)...
set /a ATTEMPTS=0

:WAIT_FRONTEND
set /a ATTEMPTS+=1
if %ATTEMPTS% GTR 30 (
    echo       AVISO: Timeout. Verifique a janela "TIP Frontend" por erros.
    goto OPEN_BROWSER
)

powershell -NoProfile -Command "try { $s=(Invoke-WebRequest -Uri 'http://127.0.0.1:%FRONTEND_PORT%/login' -UseBasicParsing -TimeoutSec 4).StatusCode; if ($s -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% equ 0 goto OPEN_BROWSER

echo       Tentativa %ATTEMPTS%/30...
timeout /t 2 /nobreak >nul
goto WAIT_FRONTEND

:OPEN_BROWSER
echo Abrindo navegador...
start "" "http://localhost:%FRONTEND_PORT%/login"

echo.
echo ========================================
echo   Sistema em execucao
echo ========================================
echo   Frontend: http://localhost:%FRONTEND_PORT%/login
echo   Backend:  http://127.0.0.1:%BACKEND_PORT%/
echo   Health:   http://127.0.0.1:%BACKEND_PORT%/health/
echo.
echo   Para encerrar, feche as janelas:
echo   - TIP Backend
echo   - TIP Frontend
echo ========================================
echo.
pause
goto :EOF

:KillPort
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%~1" ^| findstr "LISTENING"') do (
    echo       Encerrando processo PID %%p na porta %~1
    taskkill /F /PID %%p >nul 2>&1
)
goto :EOF
