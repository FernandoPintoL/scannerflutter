# Guía de Instalación y Solución de Problemas

Esta guía te ayudará a instalar correctamente las dependencias del proyecto y resolver problemas comunes de instalación.

## Requisitos Previos

- Python 3.7+ instalado (compatible con Python 3.12.0)
- pip (gestor de paquetes de Python)
- Git (opcional, para clonar el repositorio)

## Instalación Básica

1. Clona o descarga el repositorio:
   ```
   git clone <url-del-repositorio>
   cd <directorio-del-repositorio>
   ```

2. Crea un entorno virtual (recomendado):
   ```
   python -m venv venv
   ```

3. Activa el entorno virtual:
   - En Windows:
     ```
     venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Instala las dependencias:
   ```
   pip install -r requirements_fixed.txt
   ```

## Solución de Problemas Comunes

### Problema: Conflicto entre opencv-python y opencv-python-headless

**Síntoma**: Errores al importar cv2 o al ejecutar la aplicación relacionados con OpenCV.

**Solución**: Instala solo una versión de OpenCV. Para desarrollo local, usa opencv-python:

```
pip uninstall -y opencv-python opencv-python-headless
pip install opencv-python>=4.8.1.78
```

Para entornos sin interfaz gráfica (servidores), usa opencv-python-headless:

```
pip uninstall -y opencv-python opencv-python-headless
pip install opencv-python-headless>=4.8.1.78
```

### Problema: Error al instalar supervision

**Síntoma**: Errores durante la instalación del paquete supervision.

**Solución**: Asegúrate de tener instaladas las herramientas de compilación necesarias:

1. En Windows, instala Visual C++ Build Tools:
   - Descarga e instala [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - Selecciona "Herramientas de compilación de C++" durante la instalación

2. Luego intenta instalar supervision nuevamente:
   ```
   pip install supervision>=0.25.1
   ```

### Problema: Error al instalar gunicorn en Windows

**Síntoma**: Error al instalar gunicorn en Windows.

**Solución**: Gunicorn no es compatible con Windows. Para desarrollo local en Windows, puedes omitirlo:

```
pip install -r requirements_fixed.txt
```

Para producción en un servidor Linux, puedes usar gunicorn normalmente.

### Problema: Errores con versiones de paquetes

**Síntoma**: Conflictos de versiones o incompatibilidades.

**Solución**: Asegúrate de usar exactamente las versiones especificadas:

```
pip install -r requirements_fixed.txt --no-cache-dir
```

### Problema: Dependencias adicionales para el paquete de inferencia

**Síntoma**: Errores al ejecutar el paquete de inferencia relacionados con numpy o pillow.

**Solución**: Instala las dependencias adicionales requeridas por el paquete de inferencia:

```
pip install numpy>=1.26.4 pillow>=10.0.0,<11.0.0
```

### Problema: Error al instalar NumPy con Python 3.12.0

**Síntoma**: Error durante la instalación de NumPy, especialmente con versiones incompatibles, mostrando errores de compilación o instalación.

**Solución**: Utiliza específicamente NumPy 1.26.4 que es compatible con Python 3.12.0:

```
pip install numpy>=1.26.4
```

## Verificación de la Instalación

Para verificar que todas las dependencias se han instalado correctamente, ejecuta:

```
python test_imports.py
```

Este script intentará importar todos los paquetes necesarios y te mostrará cuáles se importaron correctamente y cuáles fallaron.

## Configuración Adicional

1. Crea un archivo `.env` en la raíz del proyecto con tu API key de Roboflow:
   ```
   ROBOFLOW_API_KEY=tu_api_key_aquí
   ```

2. Verifica que los directorios necesarios existan:
   ```
   mkdir -p uploads output_results
   ```

## Ejecución de la Aplicación

Una vez instaladas todas las dependencias, puedes ejecutar la aplicación:

```
python app.py
```

La aplicación estará disponible en `http://localhost:5000`
