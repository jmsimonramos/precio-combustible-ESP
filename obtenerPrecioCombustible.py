from os.path import exists
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from git import Repo
import sys
import logging as log
from yaspin import yaspin
from Utils import cargarConfiguracion, guardarConfiguracion

config = cargarConfiguracion()

DATA_PATH = config["META"]["DATA_PATH"] # Ruta donde se almacenarán los datos
LOG_PATH = config["META"]["LOG_PATH"] # Ruta donde se almacena el log

# Configuramos el log con la ruta del fichero, el modo de uso (a = añadir al final del fichero), el formato del mensaje (tiempo - tipoError - mensaje) y la prioridad mínima(DEBUG = más baja, por lo que cualquier aviso se registrará en el log)
log.basicConfig(filename=LOG_PATH, filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', datefmt=config["META"]["FORMATO_FECHA_LOG"], level=log.DEBUG)

def obtenerDatosPrecios():
    
    with yaspin(text="Obteniendo datos del precio del combustible") as spinner:
        # Realizamos una petición al servicio rest y comprobamos que se ha realizado correctamente (código de estado = 200)
        request = requests.get(config["URL"]["API_URL"])

        if request.status_code != 200:  # Mostramos un error si no se lleva a cabo la petición satisfactoriamente
            spinner.fail(config["META"]["ICONO_ERROR"])
            log.error(f"Fallo a la hora de realizar la petición. Status Code: {request.status_code}")
            sys.exit(0)

        json_data = request.json() # Formateamos el contenido de la respuesta a JSON
        spinner.ok(config["META"]["ICONO_OK"])
    
    with yaspin(text="Comprobando que los datos no son repetidos") as spinner:
    # Almacenamos por separado los valores correspondientes a la fecha de la petición y al listado de los precios de las estaciones de servicio
        try:
            fecha = json_data["Fecha"].split(" ")[0].replace("/", "-")
            #fecha = obtenerFechaUltimaModificacionWeb()
            precios = json_data["ListaEESSPrecio"]
        
            # Si dispongo de datos para ese día se para el programa para evitar duplicidades en los datos
            if yaTengoLosDatos(fecha): 
                spinner.ok(config["META"]["ICONO_OK"])
                print(f"👌 Ya se disponen de los datos para la fecha: {fecha}")
                log.info(f"Ya se disponen de los datos para la fecha: {fecha}")
                sys.exit(0)
            spinner.ok(config["META"]["ICONO_OK"])
        except Exception as e:
            spinner.fail(config["META"]["ICONO_ERROR"])
            log.error(f"Error inesperado. {e}")

    with yaspin(text="Procesando datos") as spinner:
        # Creamos un dataframe con los precios y nos quedamos únicamente con las columnas relativas a los precios del combustible
        try:
            precios_df = pd.json_normalize(precios)
            precios_df = precios_df[config["COMBUSTIBLE"]["COLUMNAS_PRECIO"]]

            # Sustituimos los valores vacíos por NaN
            precios_df = precios_df.replace("", np.NaN)

            # Insertamos una columna correspondiente a la fecha para poder distinguir entre los precios en distintos días
            precios_df.insert(0, "Fecha", fecha)

            spinner.ok(config["META"]["ICONO_OK"])
            return fecha, precios_df
        except Exception as e:
            spinner.fail(config["META"]["ICONO_ERROR"])
            log.error(f"Error inesperado. {e}")
            sys.exit(0)

def existeFicheroDatos(fecha):
    # Comprobamos si existe el fichero para ese mes. Si existe = NO es primero de mes --> No hay que crear un nuevo archivo
    # Si NO existe = ES primero de mes --> Creamos nuevo archivo
    return exists(f"{DATA_PATH}{fecha[3:]}.csv")


def guardarDatos(dataframe, fecha, esPrimero):
    # Si el DataFrame contiene los precios del primer día del mes lo guardamos en el fichero con las cabeceras. En caso contrario lo guardamos sin ellas para así ir concatenando los datos de los diferentes días del mes
    with yaspin(text="Guardando los datos en el .csv") as spinner:
        try:
            if esPrimero: 
                dataframe.to_csv(f"{DATA_PATH}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=True, index=False)
            else:
                dataframe.to_csv(f"{DATA_PATH}{fecha[3:]}.csv", sep=";",
                                encoding="utf-8", header=False, index=False, mode="a")
            spinner.ok(config["META"]["ICONO_OK"])
        except Exception as e:
            spinner.fail(config["META"]["ICONO_ERROR"])
            log.error(f"Error inesperado. {e}")
            sys.exit(0)

def obtenerFechaUltimaModificacionWeb():
    # Realizamos una petición a la página principal donde se encuentra la información del repositorio de datos (código de estado = 200)
    r_pagina_principal = requests.get(config["URL"]["MAIN_URL"])
    
    # Utilizamos la librería BeautifulSoup para realizar búsquedas en el código fuente de la página de una forma más sencilla
    soup = BeautifulSoup(r_pagina_principal.text, "html.parser")

    # Buscamos el componente en el código fuente de la página donde se encuentra la información de la última modificación de los datos.
    componente = soup.find("li", class_="resource-item").find("span", class_="icon-stack").get("title")

    # Buscamos dentro del componente la fecha de última modificación del fichero de datos. Esta fecha se encuentra en el formato dd/mm/YYYY
    # Como sólamente hay una fecha en el componente al haberlo filtrado antes, nos quedamos con el primer y único elemento de la lista de coincidencias
    ultima_modificacion_web = re.findall(r"\d{2}\/\d{2}\/\d{4}", componente)[0]

    return ultima_modificacion_web.replace("/", "-")

def commitActualizacionesPrecios(fecha):
    with yaspin(text="Actualizando repositorio local y remoto con los nuevos cambios") as spinner:
        try:
            repo = Repo(".") # Sitúo el repositorio de git desde donde lanzo el script del proyecto

            # Añado todos los cambios al staging area y hago un commit con los nuevos datos
            repo.git.add(all=True) # git add .
            repo.git.commit('-m', f'Actualizacion de precios para el día: {fecha}') # git commit -m <mensaje>
            # Hacemos push al repositorio remoto
            origin = repo.remote(name=config["META"]["REMOTO"])
            origin.push()
            spinner.ok(config["META"]["ICONO_OK"])
        except Exception as e:
            spinner.fail(config["META"]["ICONO_ERROR"])
            log.error(f"Error inesperado. {e}")
            sys.exit(0)

def registrarUltimaFechaDisponibleProyecto(fecha):
    # Cambiamos el valor del último día de datos en la configuración
    config["COMBUSTIBLE"]["ULTIMO_DIA"] = fecha
    guardarConfiguracion(config)
    
def yaTengoLosDatos(fechaActual):
    # Comprueba si la última fecha de la que se disponen datos del precio es la misma que la actual para evitar duplicidades en los datos

    return fechaActual == config["COMBUSTIBLE"]["ULTIMO_DIA"]

if __name__ == "__main__":
    # Obtenemos los datos de los precios y la fecha
    fecha, datosPrecio_df = obtenerDatosPrecios()

    # Comprobamos si existe el fichero de datos para los precios de ese mes para guardar los nuevos datos con cabecera o sin ella
    if existeFicheroDatos(fecha=fecha):
        guardarDatos(dataframe=datosPrecio_df, fecha=fecha, esPrimero=False)
    else:
        guardarDatos(dataframe=datosPrecio_df, fecha=fecha, esPrimero=True)

    # Actualizamos el valor de la última fecha de la que disponemos datos    
    registrarUltimaFechaDisponibleProyecto(fecha) 
    
    # Commiteamos los cambios y los subimos al repositorio remoto
    commitActualizacionesPrecios(fecha)