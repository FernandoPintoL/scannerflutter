from roboflow import Roboflow
from dotenv import load_dotenv
import os
from roboflow.adapters.rfapi import RoboflowError

# Cargar variables de entorno
load_dotenv()

# Obtener API key
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")

if not ROBOFLOW_API_KEY:
    print("Error: No se encontró la API key en el archivo .env")
    exit(1)

print(f"API Key: {ROBOFLOW_API_KEY[:5]}...{ROBOFLOW_API_KEY[-5:]}")

# Lista de posibles workspaces para probar
test_workspaces = [
    "ui_component_flutter",  # El workspace actual que está fallando
    "flutter-ui",
    "flutter-widgets",
    "ui-components",
    "flutter",
    "ui",
    "components",
    "widgets",
    "default"  # Muchas APIs tienen un workspace por defecto
]

# Inicializar Roboflow
rf = Roboflow(api_key=ROBOFLOW_API_KEY)

print("\nProbando acceso a diferentes workspaces:")
valid_workspaces = []

for ws_id in test_workspaces:
    try:
        print(f"\nIntentando acceder al workspace: {ws_id}")
        workspace = rf.workspace(ws_id)
        print(f"✅ Acceso exitoso al workspace: {ws_id}")
        
        # Intentar listar proyectos
        try:
            projects = workspace.project_names()
            print(f"  Proyectos disponibles: {', '.join(projects) if projects else 'Ninguno'}")
            
            for project_name in projects:
                try:
                    project = workspace.project(project_name)
                    versions = [str(v.version) for v in project.versions()]
                    print(f"    Proyecto '{project_name}' - Versiones: {', '.join(versions) if versions else 'Ninguna'}")
                    
                    # Guardar un model_id válido para sugerir
                    if versions:
                        valid_workspaces.append({
                            "workspace": ws_id,
                            "project": project_name,
                            "version": versions[0],
                            "model_id": f"{ws_id}/{project_name}/{versions[0]}"
                        })
                except Exception as e:
                    print(f"    Error al acceder al proyecto '{project_name}': {str(e)}")
        except Exception as e:
            print(f"  Error al listar proyectos: {str(e)}")
            
        # Si llegamos aquí, el workspace existe
        valid_workspaces.append({"workspace": ws_id, "model_id": f"{ws_id}/5"})
        
    except RoboflowError as e:
        print(f"❌ Error al acceder al workspace '{ws_id}': {str(e)}")
    except Exception as e:
        print(f"❌ Error inesperado al acceder al workspace '{ws_id}': {str(e)}")

print("\n" + "="*50)
if valid_workspaces:
    print("Workspaces válidos encontrados:")
    for i, ws in enumerate(valid_workspaces, 1):
        print(f"{i}. Workspace: {ws['workspace']}")
        if "project" in ws and "version" in ws:
            print(f"   Model ID sugerido: {ws['model_id']} (workspace/project/version)")
        else:
            print(f"   Model ID sugerido: {ws['model_id']} (workspace/version)")
    
    print("\nPara usar uno de estos model_ids, modifica la línea 13 en app.py:")
    print('MODEL_ID = "workspace/project/version"  # o "workspace/version"')
else:
    print("No se encontraron workspaces válidos con esta API key.")
    print("Recomendaciones:")
    print("1. Verifica que la API key sea correcta")
    print("2. Asegúrate de tener acceso a al menos un workspace en Roboflow")
    print("3. Crea un nuevo proyecto en Roboflow si es necesario")