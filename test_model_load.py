from dotenv import load_dotenv
import os
from inference import get_model

# Cargar variables de entorno
load_dotenv()

# Configuración
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = "widgets/1"  # El nuevo model_id que estamos usando

print(f"Intentando cargar el modelo con ID: {MODEL_ID}")

try:
    # Intentar cargar el modelo
    model = get_model(model_id=MODEL_ID, api_key=ROBOFLOW_API_KEY)
    print("✅ Modelo cargado exitosamente!")

    # Obtener información adicional del modelo si es posible
    try:
        model_info = model.model_info()
        print(f"\nInformación del modelo:")
        print(f"  Tipo: {model_info.get('type', 'No disponible')}")
        print(f"  Clases: {', '.join(model_info.get('classes', ['No disponible']))}")
    except Exception as e:
        print(f"\nNo se pudo obtener información adicional del modelo: {str(e)}")

except Exception as e:
    print(f"❌ Error al cargar el modelo: {str(e)}")
