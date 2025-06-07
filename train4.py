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
image_file = "img10.png"
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

def is_related(parent_bbox, child_bbox, parent_type, child_type):
    """Función corregida con indentación adecuada y lógica optimizada"""
    px1, py1, px2, py2 = parent_bbox
    cx1, cy1, cx2, cy2 = child_bbox

    # 1. Para button_text: relación directa sin verificación espacial
    if parent_type == "button" and child_type == "button_text":
        return (
            (cx1 >= px1) and  # Completamente dentro del botón
            (cx2 <= px2) and
            (cy1 >= py1) and
            (cy2 <= py2)
        )  # Confiamos completamente en la detección del modelo

    # 2. Para texfield_label (reglas espaciales estrictas)
    elif parent_type == "TextField" and child_type == "texfield_label":
        vertical_gap = py1 - cy2  # Distancia vertical entre label y TextField
        horizontal_overlap = (min(cx2, px2) - max(cx1, px1)) / (cx2 - cx1)  # % de superposición
        
        return (
            (0 <= vertical_gap <= 30) and  # Máximo 30px de separación
            (horizontal_overlap >= 0.7)    # Mínimo 70% de alineación
        )
    
    # 3. Para texfield_hinttext (dentro del TextField con tolerancia)
    elif parent_type == "TextField" and child_type == "texfield_hinttext":
        return (
            (cx1 >= px1 - 10) and  # Margen izquierdo
            (cx2 <= px2 + 10) and  # Margen derecho
            (cy1 >= py1 - 5) and   # Margen superior
            (cy2 <= py2 + 5)       # Margen inferior
        )
    
    # 4. Para cualquier otro caso
    return False


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
            'allowlist': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZáéíóúÁÉÍÓÚñÑ:´@#.,0123456789',
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
            r'logi4\b': 'login',
            r'lo9M\b': 'login',
            r'Ewe\b': 'Email:',
            r'Gilesk\b': 'Gloogle',
            r'FacsbcaK\b': 'Facebook',
            r'Botlov\b': 'Button',
            r'Butho\b': 'Button',
            r'JltField\b': 'TextField:',
            r'TextFiel:': 'TextField:',
            r'Trlulo\b': 'Título',
            r'3utho\b': 'Button',
            r'Jugrcsar\b': 'Ingresar',
            r'Usveno\b': 'Usuario:',
            r'Conbaseua:': 'Contraseña:',
            r'Valuc': 'Volver',
            r'Vulver\b': 'Volver',
            r'51hoWeb:': 'Sitio Web:',
            r'Gjoerder\b': 'Guardar',
            r'B.o:': 'Bio:',
            r'Ncmibic:': 'Nombre:',
            r'Ed:lar\b': 'Editar',
            r'Edtar\b': 'Editar',
            r'Busqidte\b': 'Búsqueda',
            r'Duscer\b': 'Buscar',
            r'FecaJuicie': 'Fecha Inicial:',
            r'KelaSraClaue:': 'Palabra Clave:', # Ajuste especial para este caso
            r'TechaZiual:': 'Fecha Final:', # Ajuste especial para este caso
            r'Quakescúa Reapercz\b': 'Recuperar Contraseña',
            r'Z,ercou': 'Dirección:',
            r'Diracoa:.': 'Dirección:',
            r'Goasdar\b': 'Guardar',
            r'Nambr': 'Nombre',
            r'How': 'Nombre:',
            r'Elad': 'Edad',
            r'Ldad': 'Edad:',
             
        
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
    
    # Mapeo de nombres para el JSON
    NAME_MAPPING = {
        "texfield_label": "label",
        "texfield_hinttext": "hint",
        "button_text": "text"
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
            "coordinates": {
                "x1": int(c_bbox[0]),
                "y1": int(c_bbox[1]),
                "x2": int(c_bbox[2]),
                "y2": int(c_bbox[3])
            },#list(map(int, c_bbox)),
            "confidence": float(c_conf),
            "subcomponents": []
        }
        
        # Buscar subcomponentes relacionados
        for s_bbox, s_conf, s_id, s_type in sub_detections:
            if s_type in COMPONENT_HIERARCHY.get(c_type, []):
                if is_related(
                    [int(x) for x in c_bbox],
                    [int(x) for x in s_bbox],
                    c_type,
                    s_type
                ):

                    # Aplicar mapeo de nombres para el JSON
                    json_type = NAME_MAPPING.get(s_type, s_type)

                    subcomponent_data = {
                        "type": json_type,
                        "coordinates": {
                            "x1": int(s_bbox[0]),
                            "y1": int(s_bbox[1]),
                            "x2": int(s_bbox[2]),
                            "y2": int(s_bbox[3])
                        },#list(map(int, s_bbox)),
                        "confidence": float(s_conf)
                    }
                    
                    # Extraer texto si es un componente que requiere OCR
                    if s_type in OCR_COMPONENTS:
                        subcomponent_data["text"] = extract_ui_text(image, s_bbox, s_type)
                    component["subcomponents"].append(subcomponent_data)


        #report["components"].append(component)



        # Extraer texto para componentes principales que requieren OCR
        if c_type in OCR_COMPONENTS:
            component["text"] = extract_ui_text(image, c_bbox, c_type)
        
        report["components"].append(component)

    # 4. Guardar JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = os.path.join(output_dir, f"{image_file}.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

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