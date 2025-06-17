import supervision as sv
import cv2
import os
import json
import re
import easyocr
import numpy as np
from datetime import datetime
from inference import get_model


class WidgetScanner:
    """
    Clase para escanear y detectar widgets de Flutter en imágenes.
    """

    # Jerarquía de componentes
    COMPONENT_HIERARCHY = {
        "TextField": ["texfield_label", "texfield_hinttext"],
        "button": ["button_text"],
        "Text": [],
        "AppBar": ["AppBar_icon", "AppBar_title"],
        "checkbox": ["checkbox_text"],
        "radio": ["radio_text"],
        "Dropdown_menu": ["value_1", "value_2", "value_3", "value_4", "value_5", "value_6", "value_7"],
        "Table": ["celda", "celda_text"],
    }

    # Componentes que requieren OCR
    OCR_COMPONENTS = ["Text", "texfield_hinttext", "texfield_label", "button_text", "AppBar_title", "checkbox_text",
                      "radio_text", "value_1", "value_2", "value_3", "value_4", "value_5", "value_6", "value_7",
                      "celda_text"]

    def __init__(self, model_id, api_key, output_dir="output_results"):
        """
        Inicializa el escáner de widgets.

        Args:
            model_id (str): ID del modelo en formato 'workspace/model_name/version' o 'workspace/version'
            api_key (str): API key de Roboflow
            output_dir (str): Directorio para guardar resultados
        """
        self.model_id = model_id
        self.api_key = api_key
        self.output_dir = output_dir
        self.model = get_model(model_id=model_id, api_key=api_key)

        # Inicializar EasyOCR (es costoso inicializarlo)
        self.reader = easyocr.Reader(['es', 'en'])  # Español e inglés

        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)

    def is_related(self, parent_bbox, child_bbox, parent_type, child_type):
        """
        Verifica la relación espacial según el tipo de componentes.

        Args:
            parent_bbox (list): Coordenadas del componente principal [x1, y1, x2, y2]
            child_bbox (list): Coordenadas del subcomponente [x1, y1, x2, y2]
            parent_type (str): Tipo del componente principal
            child_type (str): Tipo del subcomponente

        Returns:
            bool: True si están relacionados, False en caso contrario
        """

        print(f"Llamada a is_related: {parent_type} ({parent_bbox}) <-> {child_type} ({child_bbox})")

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
            return (
                    (abs((py1 + py2) / 2 - (cy1 + cy2) / 2) < 45) and
                    (abs((px1 + px2) / 2 - (cx1 + cx2) / 2) < 150)
            )

        # 3. Para texfield_hinttext (dentro del TextField con tolerancia)
        elif parent_type == "TextField" and child_type == "texfield_hinttext":
            return (
                    (cx1 >= px1 - 10) and  # Margen izquierdo
                    (cx2 <= px2 + 10) and  # Margen derecho
                    (cy1 >= py1 - 5) and  # Margen superior
                    (cy2 <= py2 + 5)  # Margen inferior
            )
        # 4. Para AppBar
        elif parent_type == "AppBar":
            if child_type == "AppBar_title":
                return (cx1 >= px1) and (cx2 <= px2) and (cy1 >= py1) and (cy2 <= py2)
            elif child_type == "AppBar_icon":
                return (cx2 <= px1 + (px2 - px1) * 0.3)
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
                return (cx1 >= px1) and (cx2 <= px2) and (cy1 >= py1)
        # 8 Para Table
        elif parent_type == "Table" and child_type == "celda":
            return (
                    (cx1 >= px1 - 10) and
                    (cx2 <= px2 + 10) and
                    (cy1 >= py1 - 10) and
                    (cy2 <= py2 + 10)
            )
        # relacion entre celda y celda_text
        elif parent_type == "celda" and child_type == "celda_text":
            return (
                    (cx1 >= px1 - 5) and
                    (cx2 <= px2 + 5) and
                    (cy1 >= py1 - 5) and
                    (cy2 <= py2 + 5)
            )
        # 8. Para cualquier otro caso
        return False

    def extract_ui_text(self, image, bbox, component_type):
        """
        Extracción de texto con ajuste fino para caracteres similares.

        Args:
            image (numpy.ndarray): Imagen de la que extraer el texto
            bbox (list): Coordenadas del componente [x1, y1, x2, y2]
            component_type (str): Tipo del componente

        Returns:
            str: Texto extraído del componente
        """
        print(f"Llamada a extract_ui_text: {component_type} ({bbox})")
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
            results = self.reader.readtext(processed, **ocr_config)
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
                r'T\u00edtulo': 'Titulo?',
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

    def organize_table_cells(cells):
        """Organiza celdas respetando:
        1. Primera celda multi-columna (original).
        2. Posiciones absolutas de columnas (nuevo para celdas faltantes).
        3. Cálculo automático de column_span (original).
        """
        if not cells:
            return []

        # --- 1. Agrupación por filas (original) ---
        sorted_cells = sorted(cells, key=lambda c: (c['coordinates']['y1'], c['coordinates']['x1']))
        ROW_THRESHOLD = 20

        rows = []
        current_row = []

        for cell in sorted_cells:
            if not current_row:
                current_row.append(cell)
            else:
                y_diff = abs(cell['coordinates']['y1'] - current_row[0]['coordinates']['y1'])
                if y_diff < ROW_THRESHOLD:
                    current_row.append(cell)
                else:
                    rows.append(sorted(current_row, key=lambda c: c['coordinates']['x1']))
                    current_row = [cell]

        if current_row:
            rows.append(sorted(current_row, key=lambda c: c['coordinates']['x1']))

        # --- 2. Detección de columnas (original + referencia de coordenadas X) ---
        if not rows:
            return []

        first_row_cells = rows[0]
        first_cell = first_row_cells[0]
        total_width = first_row_cells[-1]['coordinates']['x2'] - first_row_cells[0]['coordinates']['x1']

        # Caso especial: primera celda multi-columna (original)
        if len(first_row_cells) == 1 and (
                first_cell['coordinates']['x2'] - first_cell['coordinates']['x1']) >= total_width * 0.8:
            num_columns = 3
            column_width = total_width / num_columns
            # Generamos referencia de columnas artificialmente
            reference_columns = [first_cell['coordinates']['x1'] + i * column_width for i in range(num_columns)]
            reference_columns.append(first_cell['coordinates']['x2'])
        else:
            # Caso normal: columnas basadas en la primera fila
            num_columns = len(first_row_cells)
            column_width = total_width / num_columns
            reference_columns = [cell['coordinates']['x1'] for cell in first_row_cells]
            reference_columns.append(first_row_cells[-1]['coordinates']['x2'])

        # --- 3. Asignación de columnas (combina lógica original + nuevo col_index) ---
        organized_rows = []

        for row_idx, row in enumerate(rows):
            row_data = {
                'type': 'TableRow',
                'coordinates': {
                    'x1': min(c['coordinates']['x1'] for c in row),
                    'y1': min(c['coordinates']['y1'] for c in row),
                    'x2': max(c['coordinates']['x2'] for c in row),
                    'y2': max(c['coordinates']['y2'] for c in row)
                },
                'children': []
            }

            for cell in sorted(row, key=lambda c: c['coordinates']['x1']):
                cell_x1 = cell['coordinates']['x1']
                cell_x2 = cell['coordinates']['x2']

                # --- A) Cálculo de col_index (nuevo: basado en referencia_columns) ---
                col_index = 0
                min_distance = float('inf')
                for i, ref_x in enumerate(reference_columns[:-1]):
                    distance = abs(cell_x1 - ref_x)
                    if distance < min_distance:
                        min_distance = distance
                        col_index = i

                # --- B) Cálculo de column_span (original) ---
                col_span = round((cell_x2 - cell_x1) / column_width)
                col_span = max(1, min(col_span, num_columns - col_index))  # Asegura no pasarse

                # --- C) Caso especial: primera celda multi-columna (original) ---
                if row_idx == 0 and len(row) == 1:
                    col_span = num_columns
                    col_index = 0

                # --- Construcción de la celda (original) ---
                cell_widget = {
                    'type': 'TableCell',
                    'column': col_index,
                    'column_span': col_span,
                    'coordinates': cell['coordinates'],
                    'child': None
                }

                if cell.get('subcomponents'):
                    text_data = cell['subcomponents'][0]
                    cell_widget['child'] = {
                        'type': 'Text',
                        'text': text_data.get('text', ''),
                        'coordinates': text_data['coordinates']
                    }

                row_data['children'].append(cell_widget)

            organized_rows.append(row_data)

        return organized_rows

    def scan_image(self, image_path):
        """
        Escanea una imagen para detectar widgets de Flutter.

        Args:
            image_path (str): Ruta de la imagen a escanear

        Returns:
            dict: Reporte con los componentes detectados
            str: Ruta del archivo JSON generado
            str: Ruta de la imagen anotada
        """

        try:
            # 1. Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

            # 2. Inferencia
            results = self.model.infer(image, confidence=0.5, iou_threshold=0.7)[0]
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
                    "source_image": image_path,
                    "model_used": self.model_id
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
                "celda": "cell",
                "celda_text": "cell_text",
            }

            # Procesar componentes principales
            main_detections = [
                (bbox, conf, class_id, class_name)
                for bbox, conf, class_id, class_name in zip(
                    detections.xyxy, detections.confidence,
                    detections.class_id, detections.data['class_name']
                ) if class_name in self.COMPONENT_HIERARCHY
            ]

            # Procesar subcomponentes
            sub_detections = [
                (bbox, conf, class_id, class_name)
                for bbox, conf, class_id, class_name in zip(
                    detections.xyxy, detections.confidence,
                    detections.class_id, detections.data['class_name']
                ) if any(class_name in subs for subs in self.COMPONENT_HIERARCHY.values())
            ]

            for c_bbox, c_conf, c_id, c_type in main_detections:
                component = {
                    "type": c_type,
                    "coordinates": {
                        "x1": int(c_bbox[0]),
                        "y1": int(c_bbox[1]),
                        "x2": int(c_bbox[2]),
                        "y2": int(c_bbox[3])
                    },  # list(map(int, c_bbox)),
                    "confidence": float(c_conf),
                    # "subcomponents": []
                }

                # Procesamiento especial para tablas
                if c_type == "Table":
                    table_cells = []
                    for s_bbox, s_conf, s_id, s_type in sub_detections:
                        if s_type == "celda" and self.is_related(c_bbox, s_bbox, c_type, s_type):
                            cell_data = {
                                "type": "celda",
                                "coordinates": {
                                    "x1": int(s_bbox[0]),
                                    "y1": int(s_bbox[1]),
                                    "x2": int(s_bbox[2]),
                                    "y2": int(s_bbox[3])
                                },
                                "confidence": float(s_conf),
                                "subcomponents": []
                            }

                            # Buscar texto en la celda
                            for txt_bbox, txt_conf, txt_id, txt_type in sub_detections:
                                if txt_type == "celda_text" and self.is_related(s_bbox, txt_bbox, "celda", txt_type):
                                    text_data = {
                                        "type": "celda_text",
                                        "coordinates": {
                                            "x1": int(txt_bbox[0]),
                                            "y1": int(txt_bbox[1]),
                                            "x2": int(txt_bbox[2]),
                                            "y2": int(txt_bbox[3])
                                        },
                                        "confidence": float(txt_conf),
                                        "text": self.extract_ui_text(image, txt_bbox, txt_type)
                                    }
                                    cell_data["subcomponents"].append(text_data)

                            table_cells.append(cell_data)

                    # Organizar celdas en filas y columnas
                    component["estructure"] = {
                        "type": "Table",
                        "children": self.organize_table_cells(table_cells)
                    }
                else:
                    # Procesamiento normal para otros componentes
                    component["subcomponents"] = []
                    for s_bbox, s_conf, s_id, s_type in sub_detections:
                        if s_type in self.COMPONENT_HIERARCHY.get(c_type, []):
                            if self.is_related(c_bbox, s_bbox, c_type, s_type):
                                subcomponent_data = {
                                    "type": NAME_MAPPING.get(s_type, s_type),
                                    "coordinates": {
                                        "x1": int(s_bbox[0]),
                                        "y1": int(s_bbox[1]),
                                        "x2": int(s_bbox[2]),
                                        "y2": int(s_bbox[3])
                                    },
                                    "confidence": float(s_conf)
                                }

                                if s_type in self.OCR_COMPONENTS:
                                    subcomponent_data["text"] = self.extract_ui_text(image, s_bbox, s_type)
                                component["subcomponents"].append(subcomponent_data)

                # Extraer texto para componentes principales
                if c_type in self.OCR_COMPONENTS:
                    component["text"] = self.extract_ui_text(image, c_bbox, c_type)

                report["components"].append(component)

            # 4. Guardar JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = os.path.join(self.output_dir, f"ui_analysis_{timestamp}.json")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            # 5. Visualización
            box_annotator = sv.BoxAnnotator(thickness=2, color=sv.Color(r=0, g=255, b=0))
            label_annotator = sv.LabelAnnotator(text_scale=0.7, text_color=sv.Color.BLACK)

            labels = [
                f"{class_name} {confidence:.2f}"
                for class_name, confidence in
                zip(detections.data['class_name'], detections.confidence)
            ]

            annotated_image = box_annotator.annotate(image.copy(), detections)
            annotated_image = label_annotator.annotate(annotated_image, detections, labels=labels)

            image_filename = os.path.join(self.output_dir, f"annotated_{timestamp}.png")
            cv2.imwrite(image_filename, annotated_image)

            return report, json_filename, image_filename

        except Exception as e:
            raise Exception(f"Error al escanear imagen: {str(e)}")
