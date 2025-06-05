# Detector de Widgets Flutter

Este proyecto consiste en un sistema que reconoce diferentes tipos de widgets para Flutter a partir de imágenes. Proporciona tanto una interfaz gráfica web como una API para acceder a las funcionalidades.

## Características

- Detección de componentes UI de Flutter en imágenes
- Identificación de relaciones entre componentes y subcomponentes
- Interfaz web para subir y analizar imágenes
- API REST para integración con otros sistemas
- Generación de reportes en formato JSON
- Visualización de resultados con anotaciones

## Requisitos

- Python 3.7+
- Flask
- OpenCV
- Supervision
- Roboflow
- Dotenv

## Instalación

1. Clona este repositorio:
   ```
   git clone <url-del-repositorio>
   cd <directorio-del-repositorio>
   ```

2. Instala las dependencias:
   ```
   pip install flask opencv-python supervision roboflow python-dotenv
   ```

3. Configura tu API key de Roboflow:
   - Crea un archivo `.env` en la raíz del proyecto
   - Añade tu API key: `ROBOFLOW_API_KEY=tu_api_key_aquí`

## Uso

### Ejecutar la aplicación

```
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

### Interfaz Web

1. Accede a `http://localhost:5000` en tu navegador
2. Sube una imagen con componentes de Flutter UI
3. Visualiza los resultados del análisis

### API

#### Escanear una imagen

**Endpoint:** `POST /api/scan`

**Parámetros:**
- `file`: Archivo de imagen (PNG, JPG, JPEG)

**Ejemplo con curl:**
```
curl -X POST -F "file=@ruta/a/tu/imagen.png" http://localhost:5000/api/scan
```

**Respuesta:**
```json
{
  "success": true,
  "report": {
    "metadata": {
      "analysis_date": "2025-06-04 15:30:45",
      "source_image": "imagen1.png",
      "model_used": "ui_component_flutter/5"
    },
    "components": [
      {
        "type": "TextField",
        "coordinates": [100, 200, 300, 250],
        "confidence": 0.95,
        "subcomponents": [
          {
            "type": "texfield_label",
            "coordinates": [100, 180, 200, 195],
            "confidence": 0.92
          }
        ]
      }
    ]
  },
  "files": {
    "original_image": "http://localhost:5000/uploads/imagen1.png",
    "annotated_image": "http://localhost:5000/output/annotated_20250604_153045.png",
    "json_file": "http://localhost:5000/output/ui_analysis_20250604_153045.json"
  }
}
```

## Estructura del Proyecto

- `app.py`: Aplicación principal Flask
- `inference.py`: Módulo para cargar el modelo de Roboflow
- `scanner.py`: Clase para escanear y detectar widgets
- `templates/`: Plantillas HTML para la interfaz web
- `static/`: Archivos estáticos (CSS, JS, imágenes)
- `uploads/`: Directorio para imágenes subidas
- `output_results/`: Directorio para resultados generados
- `Procfile`: Configuración para despliegue en Railway
- `runtime.txt`: Especificación de la versión de Python
- `railway.json`: Configuración adicional para Railway

## Jerarquía de Componentes

El sistema reconoce los siguientes componentes y sus relaciones:

- TextField
  - texfield_label
  - texfield_hinttext
- button
  - button_text
- Text

## Solución de problemas con el modelo de Roboflow

Si ves un mensaje de error indicando que el modelo no está disponible, sigue estos pasos para resolver el problema:

### Verificar la API Key de Roboflow

1. Asegúrate de tener una cuenta en [Roboflow](https://roboflow.com/)
2. Obtén tu API key desde la configuración de tu cuenta
3. Actualiza el archivo `.env` con tu API key:
   ```
   ROBOFLOW_API_KEY=tu_api_key_aquí
   ```

### Verificar el ID del modelo

El error puede ocurrir porque:
- El workspace especificado no existe
- No tienes permisos para acceder al workspace
- El proyecto especificado no existe en ese workspace
- La versión especificada no existe para ese proyecto

Para encontrar un modelo válido:

1. Inicia sesión en tu cuenta de Roboflow
2. Ve a tus workspaces y proyectos
3. Selecciona un proyecto que tenga un modelo entrenado
4. Anota el ID del workspace, el nombre del proyecto y la versión del modelo
5. Actualiza la variable `MODEL_ID` en `app.py` con el formato correcto:
   ```python
   MODEL_ID = "workspace/project/version"
   ```

### Usar el script de prueba

Puedes usar el script `test_api_key.py` para verificar qué workspaces están disponibles con tu API key:

```
python test_api_key.py
```

Este script intentará acceder a varios workspaces comunes y te mostrará cuáles son accesibles.

### Crear tu propio modelo en Roboflow

Si no tienes acceso a un modelo existente, puedes crear uno:

1. Regístrate en [Roboflow](https://roboflow.com/)
2. Crea un nuevo workspace y proyecto
3. Sube algunas imágenes de interfaces de Flutter
4. Etiqueta los componentes (TextField, button, Text, etc.)
5. Entrena un modelo de detección de objetos
6. Usa el ID de tu nuevo modelo en la aplicación

## Despliegue en Railway

Este proyecto está configurado para ser desplegado fácilmente en [Railway](https://railway.app/), una plataforma de despliegue en la nube.

### Requisitos previos

1. Tener una cuenta en [Railway](https://railway.app/)
2. Tener instalado el CLI de Railway (opcional)
3. Tener un repositorio Git con el código del proyecto

### Pasos para el despliegue

1. Inicia sesión en Railway y crea un nuevo proyecto
2. Conecta tu repositorio Git o sube el código directamente
3. Railway detectará automáticamente que es una aplicación Python/Flask
4. Configura las variables de entorno:
   - `ROBOFLOW_API_KEY`: Tu API key de Roboflow
   - `FLASK_ENV`: Establece a `production` para entorno de producción
5. Despliega la aplicación

Railway utilizará los siguientes archivos para configurar el despliegue:
- `Procfile`: Define el comando para iniciar la aplicación
- `runtime.txt`: Especifica la versión de Python
- `requirements.txt`: Lista las dependencias
- `railway.json`: Configuración adicional para Railway

### Verificación del despliegue

Una vez desplegada, Railway proporcionará una URL para acceder a la aplicación. Visita esa URL para verificar que la aplicación funciona correctamente.

## Licencia

Este proyecto está licenciado bajo los términos de la licencia MIT.
