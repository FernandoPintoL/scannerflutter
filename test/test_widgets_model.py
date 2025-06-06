from dotenv import load_dotenv
import os
from inference import get_model
from roboflow.adapters.rfapi import RoboflowError

# Cargar variables de entorno
load_dotenv()

# Configuración
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
WORKSPACES = ["flutter", "ui", "components", "default"]  # Workspaces que sabemos que existen

# Función para probar un workspace
def test_workspace(workspace):
    print(f"\nProbando diferentes versiones para el workspace: {workspace}")
    print("=" * 50)

    # Probar versiones del 1 al 10
    for version in range(1, 11):
        MODEL_ID = f"{workspace}/{version}"
        print(f"\nIntentando cargar el modelo con ID: {MODEL_ID}")

        try:
            # Intentar cargar el modelo
            model = get_model(model_id=MODEL_ID, api_key=ROBOFLOW_API_KEY)
            print("✅ Modelo cargado exitosamente!")

            # Obtener información adicional del modelo si es posible
            try:
                model_info = model.model_info()
                print(f"  Tipo: {model_info.get('type', 'No disponible')}")
                print(f"  Clases: {', '.join(model_info.get('classes', ['No disponible']))}")
            except Exception as e:
                print(f"  No se pudo obtener información adicional: {str(e)}")

            print("\n¡ÉXITO! Este model_id funciona correctamente.")
            print(f"Actualiza app.py para usar MODEL_ID = \"{MODEL_ID}\"")
            return True

        except RoboflowError as e:
            print(f"❌ Error de Roboflow: {str(e)}")
        except Exception as e:
            print(f"❌ Error general: {str(e)}")

    print(f"\nNo se encontró ninguna versión válida para el workspace: {workspace}")
    return False

# Probar cada workspace
success = False
for workspace in WORKSPACES:
    if test_workspace(workspace):
        success = True
        break

if not success:
    print("\n" + "=" * 50)
    print("No se encontró ningún model_id válido en ninguno de los workspaces.")
    print("Posibles soluciones:")
    print("1. Verifica que la API key sea correcta")
    print("2. Asegúrate de tener acceso a al menos un modelo en Roboflow")
    print("3. Crea un nuevo proyecto en Roboflow si es necesario")
    print("4. Contacta al soporte de Roboflow para obtener ayuda")

print("\n" + "=" * 50)
print("Prueba completada.")
