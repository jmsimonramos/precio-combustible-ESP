import json
import pandas as pd
import numpy as np


# Carga los datos de la configuración fijados en el fichero config.json
def cargarConfiguracion(ruta="config.json"):
    with open(ruta, 'r', encoding='utf-8') as file:
        configuracion = json.load(file)
    return configuracion

# Guarda la nueva configuración en el fichero config.json
def guardarConfiguracion(configuracion, ruta="config.json"):
    with open (ruta, "w",  encoding="utf-8") as file:
        json.dump(configuracion, file, indent=4)

# Transforma los precios en formato strings con , a formato float
def formatearPrecio(precio):
    if pd.isna(precio):
        return np.nan
    return float(precio.replace(",", "."))
