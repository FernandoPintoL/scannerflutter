import os
import supervision as sv
from roboflow import Roboflow
from roboflow.adapters.rfapi import RoboflowError

def get_model(model_id, api_key):
    """
    Obtiene un modelo de Roboflow para inferencia.

    Args:
        model_id (str): ID del modelo en formato 'workspace/model_name/version' o 'workspace/version'
        api_key (str): API key de Roboflow

    Returns:
        model: Modelo de Roboflow listo para inferencia
    """
    # Extraer workspace, model_name y version_number
    parts = model_id.split('/')

    if len(parts) == 3:
        # Formato tradicional: workspace/model_name/version
        workspace, model_name, version_number = parts
    elif len(parts) == 2:
        # Formato alternativo: workspace/version
        # Usamos el workspace como nombre del proyecto también
        workspace, version_number = parts
        model_name = workspace
    else:
        raise ValueError(f"Formato de model_id incorrecto. Debe ser 'workspace/model_name/version' o 'workspace/version'. Recibido: {model_id}")

    version_number = int(version_number)

    # Inicializar Roboflow
    try:
        rf = Roboflow(api_key=api_key)
        workspace = rf.workspace(workspace)
        project = workspace.project(model_name)
        model = project.version(version_number).model
    except RoboflowError as e:
        # Proporcionar un mensaje de error más útil
        if "Workspace with ID" in str(e) and "does not exist" in str(e):
            raise ValueError(f"El workspace '{workspace}' no existe o no tienes permisos para acceder a él. Verifica tu API key y el ID del workspace.")
        elif "Project with ID" in str(e) and "does not exist" in str(e):
            raise ValueError(f"El proyecto '{model_name}' no existe en el workspace '{workspace}' o no tienes permisos para acceder a él.")
        elif "Version" in str(e) and "does not exist" in str(e):
            raise ValueError(f"La versión {version_number} no existe para el proyecto '{model_name}' en el workspace '{workspace}'.")
        else:
            # Si es otro tipo de error de Roboflow, lo propagamos con el mensaje original
            raise ValueError(f"Error de Roboflow: {str(e)}")

    return model
