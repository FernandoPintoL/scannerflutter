import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from scanner import WidgetScanner

# Cargar variables de entorno
load_dotenv()

# Configuración
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = "ui_component_flutter/5"  # Nuevo model_id que funciona correctamente según test_api_key.py
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output_results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Crear directorios si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Inicializar Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Inicializar el escáner
try:
    scanner = WidgetScanner(
        model_id=MODEL_ID,
        api_key=ROBOFLOW_API_KEY,
        output_dir=OUTPUT_FOLDER
    )
    MODEL_LOADED = True
    print(f"✅ Modelo cargado exitosamente: {MODEL_ID}")
except Exception as e:
    print(f"⚠️ Error al cargar el modelo: {str(e)}")
    print("La aplicación se ejecutará en modo limitado. No se podrán escanear imágenes.")
    print("\nPosibles soluciones:")
    print("1. Verifica que la API key en el archivo .env sea correcta")
    print("2. Asegúrate de tener acceso al modelo especificado en Roboflow")
    print("3. Modifica el MODEL_ID en app.py si es necesario")
    print("4. Ejecuta test_api_key.py para verificar la API key y obtener sugerencias de model_id")
    MODEL_LOADED = False

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Página principal con formulario de carga de imágenes"""
    return render_template('index.html', model_loaded=MODEL_LOADED, model_id=MODEL_ID)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Sirve archivos subidos"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/output/<filename>')
def output_file(filename):
    """Sirve archivos de resultados"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/scan', methods=['POST'])
def scan_image():
    """Endpoint para escanear una imagen desde la interfaz web"""
    # Verificar si el modelo está cargado
    if not MODEL_LOADED:
        return render_template('error.html', error='El modelo no está disponible. Por favor, verifica la configuración de la API key y el model_id.'), 503

    # Verificar si hay un archivo en la solicitud
    if 'file' not in request.files:
        return render_template('error.html', error='No se seleccionó ningún archivo'), 400

    file = request.files['file']

    # Verificar si el usuario seleccionó un archivo
    if file.filename == '':
        return render_template('error.html', error='No se seleccionó ningún archivo'), 400

    # Verificar si el archivo es válido
    if file and allowed_file(file.filename):
        # Guardar el archivo
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Escanear la imagen
            report, json_path, image_path = scanner.scan_image(file_path)

            # Extraer solo los nombres de archivo de las rutas completas
            json_filename = os.path.basename(json_path)
            image_filename = os.path.basename(image_path)

            # Renderizar la página de resultados
            return render_template(
                'result.html',
                original_image=url_for('uploaded_file', filename=filename),
                annotated_image=url_for('output_file', filename=image_filename),
                json_file=url_for('output_file', filename=json_filename),
                report=report
            )

        except Exception as e:
            return render_template('error.html', error=str(e)), 500

    return render_template('error.html', error='Tipo de archivo no permitido'), 400

@app.route('/api/scan', methods=['POST'])
def api_scan_image():
    """API endpoint para escanear una imagen"""
    # Verificar si el modelo está cargado
    if not MODEL_LOADED:
        return jsonify({
            'error': 'El modelo no está disponible. Por favor, verifica la configuración de la API key y el model_id.',
            'model_status': 'not_loaded',
            'model_id': MODEL_ID
        }), 503

    # Verificar si hay un archivo en la solicitud
    if 'file' not in request.files:
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    file = request.files['file']

    # Verificar si el usuario seleccionó un archivo
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    # Verificar si el archivo es válido
    if file and allowed_file(file.filename):
        # Guardar el archivo
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Escanear la imagen
            report, json_path, image_path = scanner.scan_image(file_path)

            # Extraer solo los nombres de archivo de las rutas completas
            json_filename = os.path.basename(json_path)
            image_filename = os.path.basename(image_path)

            # Construir URLs para los archivos generados
            base_url = request.host_url.rstrip('/')

            # Preparar respuesta JSON
            response = {
                'success': True,
                'report': report,
                'files': {
                    'original_image': f"{base_url}/uploads/{filename}",
                    'annotated_image': f"{base_url}/output/{image_filename}",
                    'json_file': f"{base_url}/output/{json_filename}"
                }
            }

            return jsonify(response)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # In production, debug should be False
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
