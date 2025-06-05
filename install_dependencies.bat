@echo off
echo ===================================================
echo Instalador de Dependencias para Detector de Widgets
echo ===================================================
echo.

REM Verificar si Python está instalado
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en el PATH.
    echo Por favor, instala Python 3.7+ desde https://www.python.org/downloads/
    echo y asegúrate de marcar la opción "Add Python to PATH" durante la instalación.
    pause
    exit /b 1
)

REM Verificar si pip está instalado
pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip no está instalado o no está en el PATH.
    echo Por favor, reinstala Python y asegúrate de incluir pip.
    pause
    exit /b 1
)

echo Creando entorno virtual...
if exist venv (
    echo El entorno virtual ya existe. Usándolo...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

echo Activando entorno virtual...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

echo Actualizando pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ADVERTENCIA: No se pudo actualizar pip, pero continuaremos con la instalación.
)

echo Desinstalando versiones anteriores de OpenCV para evitar conflictos...
pip uninstall -y opencv-python opencv-python-headless
echo.

echo Instalando dependencias principales...
pip install flask==2.3.3 Werkzeug==2.3.7 python-dotenv==1.0.0 roboflow==1.1.9
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias principales.
    pause
    exit /b 1
)

echo Instalando OpenCV (versión con GUI para desarrollo local)...
pip install opencv-python==4.8.1.78
if %errorlevel% neq 0 (
    echo ERROR: No se pudo instalar opencv-python.
    echo Intenta instalar las herramientas de compilación de Visual C++.
    pause
    exit /b 1
)

echo Instalando supervision...
pip install supervision==0.25.1
if %errorlevel% neq 0 (
    echo ERROR: No se pudo instalar supervision.
    echo Es posible que necesites instalar Visual C++ Build Tools.
    echo Visita: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo Selecciona "Herramientas de compilación de C++" durante la instalación.
    echo Luego ejecuta este script nuevamente.
    pause
    exit /b 1
)

echo Intentando instalar gunicorn (opcional, puede fallar en Windows)...
pip install gunicorn==21.2.0
if %errorlevel% neq 0 (
    echo ADVERTENCIA: No se pudo instalar gunicorn. Esto es normal en Windows y no afecta el desarrollo local.
)

echo Creando directorios necesarios...
if not exist uploads mkdir uploads
if not exist output_results mkdir output_results

echo Verificando la instalación...
python test_imports.py
if %errorlevel% neq 0 (
    echo ADVERTENCIA: La verificación de importaciones falló. Revisa los errores específicos arriba.
) else (
    echo ¡Instalación completada con éxito!
)

echo.
echo ===================================================
echo Pasos adicionales:
echo 1. Crea un archivo .env con tu API key de Roboflow:
echo    ROBOFLOW_API_KEY=tu_api_key_aquí
echo.
echo 2. Ejecuta la aplicación:
echo    python app.py
echo ===================================================
echo.

pause
