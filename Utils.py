import json
from textwrap import indent

# Carga los datos de la configuración fijados en el fichero config.json
def cargarConfiguracion(ruta="config.json"):
    with open(ruta, 'r', encoding='utf-8') as file:
        configuracion = json.load(file)
    return configuracion

def guardarConfiguracion(configuracion, ruta="config.json"):
    with open (ruta, "w",  encoding="utf-8") as file:
        json.dump(configuracion, file, indent=4)
