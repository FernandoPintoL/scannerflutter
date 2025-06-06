from inference import get_model
import supervision as sv
import cv2
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
import re
import easyocr  # Reemplazamos pytesseract con easyocr

load_dotenv()

# Configuración
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
image_file = "imagen1.png"
model_id = "ui_component_flutter/5"
output_dir = "output_results"
os.makedirs(output_dir, exist_ok=True)

# Inicializar EasyOCR una sola vez (es costoso inicializarlo)
reader = easyocr.Reader(['es', 'en'])  # Español e inglés

# Jerarquía de componentes
COMPONENT_HIERARCHY = {
    "TextField": ["texfield_label", "texfield_hinttext"],
    "button": ["button_text"],
    "Text": [],
}

# Componentes que requieren OCR
OCR_COMPONENTS = ["Text", "texfield_hinttext", "texfield_label", "button_text"]

def is_related(component_bbox, sub_bbox, component_type, subcomponent_type):
    """Verifica la relación espacial según el tipo de componentes"""
    cx1, cy1, cx2, cy2 = component_bbox
    sx1, sy1, sx2, sy2 = sub_bbox
    
    # Caso especial: textfield_label encima del TextField
    if component_type == "TextField" and subcomponent_type == "texfield_label":
        return (sy2 < cy1) and (abs((sx1+sx2)/2 - (cx1+cx2)/2)) < (cx2-cx1)/2
    
    # Comportamiento por defecto
    return (sx1 >= cx1) and (sy1 >= cy1) and (sx2 <= cx2) and (sy2 <= cy2)

def extract_ui_text(image, bbox, component_type):
    """Extracción de texto con ajuste fino para caracteres similares"""
    try:
        x1, y1, x2, y2 = map(int, bbox)
        roi = image[y1:y2, x1:x2]
        
        # 1. Preprocesamiento ligero pero efectivo
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, processed = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        
        # 2. Configuración hiper-específica para tu caso
        ocr_config = {
            'detail': 0,
            'text_threshold': 0.65,
            'width_ths': 1.2,
            'allowlist': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZáéíóúÁÉÍÓÚñÑ:',
            'min_size': 20,  # Filtrar ruido pequeño
            'slope_ths': 0.1  # Para texto bien horizontal
        }
        
        # 3. Ejecución con post-procesamiento inteligente
        results = reader.readtext(processed, **ocr_config)
        raw_text = " ".join(results).strip()
        
        # 4. Correcciones basadas en patrones visuales
        correction_rules = {
            r'Invler\b': 'Invitar',
            r'Coveo:': 'Correo:',
            r'Correc\b': 'Correo',
            r'logi\b': 'login',
            r'Ewe\b': 'email:',
            r'Gilesk\b': 'gloogle',
            r'FacsbcaK\b': 'facebook',
        
        }
        
        for pattern, correction in correction_rules.items():
            raw_text = re.sub(pattern, correction, raw_text)
        
        return raw_text if raw_text else ""
    
    except Exception as e:
        print(f"⚠️ Error mínimo: {str(e)}")
        return ""
    
   

try:
    # 1. Cargar imagen
    image = cv2.imread(image_file)
    if image is None:
        raise FileNotFoundError(f"Imagen no encontrada: {image_file}")

    # 2. Inferencia
    model = get_model(model_id=model_id, api_key=ROBOFLOW_API_KEY)
    results = model.infer(image)[0]
    detections = sv.Detections.from_inference(results)

    # 3. Estructura del reporte
    report = {
        "metadata": {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_image": image_file,
            "model_used": model_id
        },
        "components": []
    }

    # Procesar componentes principales
    main_detections = [
        (bbox, conf, class_id, class_name) 
        for bbox, conf, class_id, class_name in zip(
            detections.xyxy, detections.confidence,
            detections.class_id, detections.data['class_name']
        ) if class_name in COMPONENT_HIERARCHY
    ]

    # Procesar subcomponentes
    sub_detections = [
        (bbox, conf, class_id, class_name) 
        for bbox, conf, class_id, class_name in zip(
            detections.xyxy, detections.confidence,
            detections.class_id, detections.data['class_name']
        ) if any(class_name in subs for subs in COMPONENT_HIERARCHY.values())
    ]

    for c_bbox, c_conf, c_id, c_type in main_detections:
        component = {
            "type": c_type,
            "coordinates": list(map(int, c_bbox)),
            "confidence": float(c_conf),
            "subcomponents": []
        }
        
        # Buscar subcomponentes relacionados
        for s_bbox, s_conf, s_id, s_type in sub_detections:
            if s_type in COMPONENT_HIERARCHY.get(c_type, []):
                if is_related(
                    list(map(int, c_bbox)),
                    list(map(int, s_bbox)),
                    c_type,
                    s_type
                ):
                    subcomponent_data = {
                        "type": s_type,
                        "coordinates": list(map(int, s_bbox)),
                        "confidence": float(s_conf)
                    }
                    
                    # Extraer texto si es un componente que requiere OCR
                    if s_type in OCR_COMPONENTS:
                        subcomponent_data["text"] = extract_ui_text(image, s_bbox, s_type)
                    
                    component["subcomponents"].append(subcomponent_data)
        
        # Extraer texto para componentes principales que requieren OCR
        if c_type in OCR_COMPONENTS:
            component["text"] = extract_ui_text(image, c_bbox, c_type)
        
        report["components"].append(component)

    # 4. Guardar JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = os.path.join(output_dir, f"{image_file}.json")
    with open(json_filename, 'w') as f:
        json.dump(report, f, indent=2)

    # 5. Visualización (opcional)
    box_annotator = sv.BoxAnnotator(thickness=2, color=sv.Color(r=0, g=255, b=0))
    label_annotator = sv.LabelAnnotator(text_scale=0.7, text_color=sv.Color.BLACK)
    
    labels = [
        f"{class_name} {confidence:.2f}" 
        for class_name, confidence in 
        zip(detections.data['class_name'], detections.confidence)
    ]
    
    annotated_image = box_annotator.annotate(image.copy(), detections)
    annotated_image = label_annotator.annotate(annotated_image, detections, labels=labels)
    
    image_filename = os.path.join(output_dir, f"annotated_{image_file}.png")
    cv2.imwrite(image_filename, annotated_image)
    
    print(f"\n✅ Procesamiento completado:")
    print(f"- Reporte JSON guardado en: {json_filename}")
    print(f"- Imagen anotada guardada en: {image_filename}")

except Exception as e:
    print(f"❌ Error: {str(e)}")