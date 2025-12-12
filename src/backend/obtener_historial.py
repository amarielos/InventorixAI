import json
import pandas as pd

def obtener_historial():
    historial_path = "data/historial.json"

    # Leer historial
    with open(historial_path, "r") as file:
        datos = json.load(file)

    # Convertir a DataFrame
    df = pd.DataFrame(datos)

    return df
