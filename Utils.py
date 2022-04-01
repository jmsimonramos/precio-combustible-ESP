import json

# Carga los datos de la configuración fijados en el fichero config.json
def cargarConfiguracion(ruta="config.json"):
    with open(ruta, 'r', encoding='utf-8') as file:
        configuracion = json.load(file)
    return configuracion
