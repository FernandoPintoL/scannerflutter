from inference import get_model
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = "ui_component_flutter/5"

try:
    print(f"Intentando cargar el modelo con ID: {MODEL_ID}")
    model = get_model(model_id=MODEL_ID, api_key=ROBOFLOW_API_KEY)
    print("¡Modelo cargado exitosamente!")
except Exception as e:
    print(f"Error al cargar el modelo: {str(e)}")