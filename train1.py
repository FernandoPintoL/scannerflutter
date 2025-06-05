from inference import get_model
import supervision as sv
import cv2
import os
import json
from dotenv import load_dotenv
import easyocr
import numpy as np
from datetime import datetime

SUPPORTED_LANGUAGES = ['es', 'en']
LANGUAGE_PRIORITY = 'es' # Prioridad para el idioma español

# Cargar variables de entorno
load_dotenv()

# Configuración inicial
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
if not ROBOFLOW_API_KEY:
    raise ValueError("API Key no encontrada. Crea un archivo .env con ROBOFLOW_API_KEY=tu_clave")

image_file = "img10.png"
model_id = "ui_component_flutter/5"
output_dir = "output_results"
os.makedirs(output_dir, exist_ok=True)

# Inicializar OCR
reader = easyocr.Reader(SUPPORTED_LANGUAGES)

try:
    # Cargar y verificar imagen
    image = cv2.imread(image_file)
    if image is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {image_file}")

    # Cargar modelo y realizar inferencia
    model = get_model(model_id=model_id)
    results = model.infer(image)[0]
    detections = sv.Detections.from_inference(results)

    # Estructura para los resultados JSON
    report_data = {
        "metadata": {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_image": image_file,
            "model_used": model_id
        },
        "components": {
            "textfield": [],
            "buttons": [],
            "text": []
        }
    }

    # Función mejorada para extracción de texto
    def extract_text(roi, is_label=False):
        if roi.size == 0:
            return ""
        
        # Preprocesamiento diferente para labels vs contenido
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        if is_label:
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        text = reader.readtext(gray, detail=0, paragraph=True)
        return " ".join(text) if text else ""

    # Procesamiento de cada componente
    for bbox, confidence, class_id, class_name in zip(
        detections.xyxy, detections.confidence,
        detections.class_id, detections.data.get('class_name', [])
    ):
        x1, y1, x2, y2 = map(int, bbox)
        component = {
            "coordinates": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "confidence": float(confidence),
            "detected_text": ""
        }

        roi = image[y1:y2, x1:x2]
        component["detected_text"] = extract_text(roi)

        if class_name == "TextField":
            # Extraer áreas específicas del TextField
            label_roi = image[max(y1-30,0):y1, x1:x2]  # Área superior
            hint_roi = image[y1+5:y1+30, x1+5:x2-5] if (y2-y1) > 30 else roi  # Área interior superior
            
            component.update({
                "texfield_label": extract_text(label_roi, is_label=True),
                "texfield_hinttext": extract_text(hint_roi)
            })
            report_data["components"]["textfield"].append(component)
        
        elif class_name == "button":
            report_data["components"]["buttons"].append(component)
        
        elif class_name == "Text":
            report_data["components"]["text"].append(component)

    # Generar nombres de archivos con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = os.path.join(output_dir, f"ui_analysis_{timestamp}.json")
    image_filename = os.path.join(output_dir, f"annotated_{timestamp}.png")

    # Guardar JSON
    with open(json_filename, 'w') as f:
        json.dump(report_data, f, indent=2)
    print(f"\nReporte JSON guardado en: {json_filename}")

    # Visualización (manteniendo tu formato original)
    annotator = sv.BoxAnnotator(
        thickness=2,
        color=sv.Color(r=0, g=255, b=0)
    )
    label_annotator = sv.LabelAnnotator(
        text_scale=0.5,
        text_thickness=1,
        text_color=sv.Color.WHITE
    )
    
    annotated_image = annotator.annotate(image.copy(), detections)
    annotated_image = label_annotator.annotate(annotated_image, detections)
    
    cv2.imwrite(image_filename, annotated_image)
    print(f"Imagen anotada guardada en: {image_filename}")

    # Mostrar resultados
    cv2.imshow("Componentes UI Detectados", annotated_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Mostrar resumen en consola
    print("\nResumen de detección:")
    print(f"- TextFields detectados: {len(report_data['components']['textfield'])}")
    print(f"- Buttons detectados: {len(report_data['components']['buttons'])}")
    print(f"- Text elements detectados: {len(report_data['components']['text'])}")

except Exception as e:
    print(f"Error durante el análisis: {str(e)}")