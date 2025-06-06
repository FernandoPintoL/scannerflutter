# Guía de Despliegue en Railway con Python 3.12.0

Este documento proporciona instrucciones para desplegar la aplicación Scanner en Railway utilizando Python 3.12.0.

## Cambios Realizados

Para preparar la aplicación para el despliegue en Railway, se han realizado los siguientes cambios:

1. **Corregido el archivo nixpacks.toml**: Se corrigió un error tipográfico en la primera línea del archivo, cambiando `#nickpacks.toml` a `#nixpacks.toml`.

2. **Actualizado el entorno a producción**: Se cambió `FLASK_ENV=development` a `FLASK_ENV=production` en el archivo `.env` para asegurar que la aplicación se ejecute en modo producción.

## Configuración de Railway

Para desplegar correctamente la aplicación en Railway, sigue estos pasos:

1. **Crear un nuevo proyecto en Railway**:
   - Inicia sesión en [Railway](https://railway.app/)
   - Crea un nuevo proyecto
   - Selecciona "Deploy from GitHub repo"
   - Conecta tu repositorio de GitHub

2. **Configurar variables de entorno**:
   En la sección "Variables" de tu proyecto en Railway, configura las siguientes variables:
   - `ROBOFLOW_API_KEY`: Tu clave API de Roboflow
   - `PORT`: 5000 (o el puerto que prefieras)
   - `FLASK_ENV`: production

3. **Verificar la configuración de despliegue**:
   - Railway detectará automáticamente que es una aplicación Python gracias al archivo `nixpacks.toml`
   - El archivo `runtime.txt` especifica Python 3.12.0
   - El archivo `.railwayignore` excluye correctamente el paquete pywin32 que es específico de Windows

## Estructura de Archivos Importantes

- **app.py**: Aplicación principal de Flask
- **scanner.py**: Contiene la lógica para escanear imágenes
- **requirements.txt**: Lista de dependencias
- **runtime.txt**: Especifica Python 3.12.0
- **nixpacks.toml**: Configuración de construcción para Railway
- **.env**: Variables de entorno locales (no se sube a Railway)
- **.railwayignore**: Archivos a ignorar durante el despliegue

## Notas Importantes

1. **Directorios temporales**: Los directorios `uploads` y `output_results` se crean automáticamente si no existen, pero ten en cuenta que Railway tiene un sistema de archivos efímero. Los archivos subidos y generados se perderán cuando la instancia se reinicie.

2. **Modelo de Roboflow**: Asegúrate de que el modelo especificado en `app.py` (`ui_component_flutter/5`) esté disponible con tu clave API de Roboflow.

3. **Monitoreo**: Una vez desplegada, monitorea los logs de Railway para asegurarte de que la aplicación se inicia correctamente y el modelo se carga sin errores.

## Solución de Problemas

Si encuentras problemas durante el despliegue:

1. **Error de carga del modelo**: Verifica que la API key de Roboflow sea correcta y que tengas acceso al modelo especificado.

2. **Errores de dependencias**: Si hay problemas con alguna dependencia, puedes modificar el archivo `nixpacks.toml` para incluir paquetes adicionales en la sección `nixPkgs`.

3. **Problemas de puerto**: Railway asigna automáticamente un puerto a tu aplicación a través de la variable de entorno `PORT`. Asegúrate de que tu aplicación esté configurada para escuchar en este puerto.