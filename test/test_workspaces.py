from roboflow import Roboflow
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Obtener API key
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")

if not ROBOFLOW_API_KEY:
    print("Error: No se encontró la API key en el archivo .env")
    exit(1)

try:
    print("Conectando a Roboflow...")
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    
    print("\nWorkspaces disponibles:")
    workspaces = rf.workspaces()
    
    if not workspaces:
        print("No se encontraron workspaces disponibles con esta API key.")
    else:
        for i, workspace in enumerate(workspaces, 1):
            print(f"{i}. ID: {workspace.id}, Nombre: {workspace.name}")
            
            print(f"\nProyectos en workspace '{workspace.name}':")
            projects = workspace.projects()
            
            if not projects:
                print("  No hay proyectos en este workspace.")
            else:
                for j, project in enumerate(projects, 1):
                    print(f"  {j}. ID: {project.id}, Nombre: {project.name}")
                    
                    print(f"    Versiones disponibles:")
                    versions = project.versions()
                    
                    if not versions:
                        print("      No hay versiones disponibles.")
                    else:
                        for k, version in enumerate(versions, 1):
                            print(f"      {k}. Versión: {version.version}, Estado: {version.status}")
    
    print("\nSugerencia de model_id para usar en la aplicación:")
    if workspaces and workspaces[0].projects() and workspaces[0].projects()[0].versions():
        workspace = workspaces[0]
        project = workspace.projects()[0]
        version = project.versions()[0].version
        print(f"{workspace.id}/{project.id}/{version}")
    else:
        print("No se pudo generar una sugerencia de model_id porque no hay suficientes datos disponibles.")
        
except Exception as e:
    print(f"Error al conectar con Roboflow: {str(e)}")