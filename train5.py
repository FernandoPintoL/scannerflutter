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
image_file = "img04.png"
model_id = "ui_component_flutter/13"
output_dir = "output_results"
os.makedirs(output_dir, exist_ok=True)

# Inicializar EasyOCR una sola vez (es costoso inicializarlo)
reader = easyocr.Reader(['es', 'en'])  # Español e inglés

# Jerarquía de componentes
COMPONENT_HIERARCHY = {
    "TextField": ["texfield_label", "texfield_hinttext"],
    "button": ["button_text"],
    "Text": [],
    "AppBar": ["AppBar_icon", "AppBar_title"],
    "checkbox": ["checkbox_text"],
    "radio": ["radio_text"],
    "Dropdown_menu": ["value_1", "value_2", "value_3", "value_4", "value_5", "value_6", "value_7"],
}

# Componentes que requieren OCR
OCR_COMPONENTS = ["Text", "texfield_hinttext", "texfield_label", "button_text", "AppBar_title", "checkbox_text", "radio_text", "value_1", "value_2", "value_3", "value_4", "value_5", "value_6", "value_7"]

def is_related(parent_bbox, child_bbox, parent_type, child_type):
    """Función corregida con indentación adecuada y lógica optimizada"""
    px1, py1, px2, py2 = parent_bbox
    cx1, cy1, cx2, cy2 = child_bbox

    # 1. Para button_text: relación directa sin verificación espacial
    if parent_type == "button" and child_type == "button_text":
        return (
            (cx1 >= px1) and  
            (cx2 <= px2) and
            (cy1 >= py1) and
            (cy2 <= py2)
        )  #

    # 2. Para texfield_label (reglas espaciales estrictas)
    elif parent_type == "TextField" and child_type == "texfield_label":
         return (
            (abs((py1 + py2)/2 - (cy1 + cy2)/2) < 45) and  
            (abs((px1 + px2)/2 - (cx1 + cx2)/2) < 150)      
        )
    # 3. Para texfield_hinttext (dentro del TextField con tolerancia)
    elif parent_type == "TextField" and child_type == "texfield_hinttext":
        return (
            (cx1 >= px1 - 10) and 
            (cx2 <= px2 + 10) and  
            (cy1 >= py1 - 5) and   
            (cy2 <= py2 + 5)       
        )

    # 4. Para AppBar
    elif parent_type == "AppBar":
        if child_type == "AppBar_title":
            return (cx1 >= px1) and (cx2 <= px2) and (cy1 >= py1) and (cy2 <= py2)
        elif child_type == "AppBar_icon":
            return (cx2 <= px1 + (px2-px1)*0.3)
            # Icono dentro del 30% izquierdo del AppBar
    
    # 5. Para checkbox
    elif parent_type == "checkbox" and child_type == "checkbox_text":
         return (
            (cx1 >= px1) and              
            (cx2 <= px2) and       
            (cy1 >= py1) and         
            (cy2 <= py2)            
        ) 
    
    # 6. Para radio
    elif parent_type == "radio" and child_type == "radio_text":
         return (
            (cx1 >= px1) and              
            (cx2 <= px2) and        
            (cy1 >= py1) and         
            (cy2 <= py2)            
        )  

    # 7. Para Dropdown_menu
    elif parent_type == "Dropdown_menu":
        if child_type.startswith("value_"):
           
            return ( cx1 >= px1) and (cx2 <= px2) and (cy1 >= py1) 
         
    
    # 8. Para cualquier otro caso
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
            r'Trtulo\b': 'Título', 
            r'TextFel\b': 'TextField', 
            r'IatField\b': 'TextField:',
            r'3utho\b': 'Button',
            r'Botlov\b': 'Button', 
            r'Passwuord:': 'Password:',
            r'Uscorio\b': 'Usuario:', 
            r'Espalcl\b': 'Español', 
            r'Jvsies\b': 'Ingles',  
            r'Chic\b': 'Chino',
            r'ceaJ\b': 'Acepto',
            r'Civdad\b': 'Ciudad',
            r'SanfaGe\b': 'Santa Cruz',
            r'LaPe:': 'La Paz',
            r'Crcha\b': 'Cocha',
            r'Apailndo:': 'Apellido:',
            r'Nomke:': 'Nombre:',
            r'logv4\b': 'Login',
            r'Jusscaar\b': 'Ingresar',
            r'Usveno': 'Usuario:',
            r'Conbasea:': 'Contraseña:',
            r'5i': 'Si',
            r'Mo': 'No',
            r'Cvestionario\b': 'Cuestionario',
            r'Oczoacen2': 'Ocupación:',
            r'2 Trabeja\b': 'Trabaja?',
            r'Csluda2\b': 'Estudia?',
            r'Edad': 'Edad:',
            r'Edlar\b': 'Editar',
            r'Guysdar\b': 'Guardar',
            r'Nambr': 'Nombre',
            r'Hlow': 'Nombre:',
            r'Dukescua Recpercz\b': 'Recuperar Contraseña',
            r'Ldad': 'Edad:',
            r'Eld': 'Edad',
            r'Zjercou': 'Dirección:',
            r'Diracoa:.': 'Dirección:',
            r'Idicme\b': 'Idioma',
            r'csPañcl\b': 'Español',
            r'Imales\b': 'Ingles',
            r'Raibic\b': 'Recibir',
            r'Possucrd:': 'Password:',
            r'Consvlle\b': 'Consulta',
            r'Hed:ca\b': 'Medica',
            r'S:': 'Si',
            r'to Regis\b': 'Registro',
            r'Enuiar\b': 'Enviar',
            r'Can#dad:': 'Cantidad:',
            r'Pcducho:': 'Producto:',
            r'EMvic2\b': 'Envio?',
            r'odocto\b': 'Producto',
            r'Fiossk\b': 'Gloogle',
            r'FacsbmK\b': 'Facebook',
            r'We::': 'Email:',
            r'logv\b': 'Login',
            r'Cuevt\b': 'Cuenta',
            r'Ancrro\b': 'Ahorro',
            r'C:': 'Ci:',
            r'Crrec\b': 'Correo',
            r'Coentas\b': 'Cuentas',
            r'Nombe': 'Nombre',
            r'Acllido': 'Apellido:',
            r'Enuio2\b': 'Envio?',
            r'A pellido': 'Apellido',
            r'Consvll2\b': 'Consulta',
            r'5í\b': 'Si',
            r'Casult\b': 'Consulta',
            r'Uombr2': 'Nombre',
            r'Ncmbre': 'Nombre:',
            r'Asisfevcia2 Rre\b': 'Pre Asistencia?',
            r'Cuevfa\b': 'Cuenta',
            r'Enuio\b': 'Envio?',
            r'Nombxe': 'Nombre',
            r'C\b': 'Ci:',
            r'Allido': 'Apellido:',
            r'Ci:uenta\b': 'Cuenta',
            r'Ci:redito\b': 'Credito',
            r'Ci:orreo\b': 'Correo',
            r'Ci:uentas\b': 'Cuentas',
            r'horro\b': 'Ahorro',
            r'Gioerder\b': 'Guardar',
            r'Bxo:': 'Bio:',
            r'SihoWeb:': 'Sitio Web:',
            r'Ncmbrc:': 'Nombre:',
            r'Ed:Yar\b': 'Editar',
            r'Duscer\b': 'Buscar',
            r'Busquede\b': 'Búsqueda',
            r'FechaZual:': 'Fecha Inicia:',
            r'alaSraClau:': 'Palabra Clave:',
            r'FecheJuicie': 'Fecha Final:',
            r'Invlar\b': 'Invitar',
            r'Aviqo\b': 'Amigo',
            r'Coveo:': 'Correo:',
            r'Correc': 'Correo',
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
    results = model.infer(image, confidence=0.5, iou_threshold=0.7)[0]
    detections = sv.Detections.from_inference(results)


      # --- INICIO: Nuevo bloque para filtrar AppBar duplicados ---
    appbar_icon_indices = [
        i for i, class_name in enumerate(detections.data['class_name']) 
        if class_name == "AppBar_icon"  # Asegúrate que coincida con el nombre de Roboflow
    ]
    
    if len(appbar_icon_indices) > 1:
        # Conservar solo el AppBar_icon con mayor confianza
        best_idx = max(
            appbar_icon_indices, 
            key=lambda i: detections.confidence[i]
        )
        
        # Filtrar detecciones (eliminar otros AppBars)
        mask = np.ones(len(detections), dtype=bool)
        mask[appbar_icon_indices] = False
        mask[best_idx] = True  # Mantener el mejor AppBar
        
        detections = sv.Detections(
            xyxy=detections.xyxy[mask],
            confidence=detections.confidence[mask],
            class_id=detections.class_id[mask],
            data={'class_name': np.array(detections.data['class_name'])[mask]}
        )
    # --- FIN: Bloque de filtrado ---

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
        "button_text": "text",
        "AppBar_title": "title",
        "AppBar_icon": "icon",
        "checkbox_text": "text",
        "radio_text": "text",
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
    
    image_filename = os.path.join(output_dir, f"annotated_{image_file}")
    cv2.imwrite(image_filename, annotated_image)
    
    print(f"\n✅ Procesamiento completado:")
    print(f"- Reporte JSON guardado en: {json_filename}")
    print(f"- Imagen anotada guardada en: {image_filename}")

except Exception as e:
    print(f"❌ Error: {str(e)}")