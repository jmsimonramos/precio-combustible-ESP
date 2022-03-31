from os.path import exists
import requests
import pandas as pd
import numpy as np
from git import Repo
import sys
import logging as log
from yaspin import yaspin

DATA_PATH = "data/historico/precioEESS-" # Ruta donde se almacenarán los datos
LOG_PATH="./app.log"

log.basicConfig(filename=LOG_PATH, filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%y %H:%M:%S', level=log.DEBUG)

def obtenerDatosPrecios():
    
    with yaspin(text="Obteniendo datos del precio del combustible") as spinner:
        # Realizamos una petición al servicio rest y comprobamos que se ha realizado correctamente (código de estado = 200)
        request = requests.get(
            "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/")

        if request.status_code != 200:  # Mostramos un error si no se lleva a cabo la petición satisfactoriamente
            spinner.fail("❌")
            log.error(f"Fallo a la hora de realizar la petición. Status Code: {request.status_code}")
            sys.exit(0)

        json_data = request.json() # Formateamos el contenido de la respuesta a JSON
        spinner.ok("✅")
    
    with yaspin(text="Comprobando que los datos no son repetidos") as spinner:
    # Almacenamos por separado los valores correspondientes a la fecha de la petición y al listado de los precios de las estaciones de servicio
        try:
            fecha = json_data["Fecha"].split(" ")[0].replace("/", "-")
            precios = json_data["ListaEESSPrecio"]
        
            # Si dispongo de datos para ese día se para el programa para evitar duplicidades en los datos
            if comprobarYaActualizado(fecha): 
                spinner.ok("✅")    
                print(f"👌 Ya se disponen de los datos para la fecha: {fecha}")
                log.info(f"Ya se disponen de los datos para la fecha: {fecha}")
                sys.exit(0)
            spinner.ok("✅")
        except Exception as e:
            spinner.fail("❌")
            log.error(f"Error inesperado. {e}")

    with yaspin(text="Procesando datos") as spinner:
        # Creamos un dataframe con los precios y nos quedamos únicamente con las columnas relativas a los precios del combustible
        try:
            precios_df = pd.json_normalize(precios)
            precios_df = precios_df[["IDEESS", "Precio Biodiesel", "Precio Bioetanol", "Precio Gas Natural Comprimido", "Precio Gas Natural Licuado", "Precio Gases licuados del petróleo", "Precio Gasoleo A", "Precio Gasoleo B",
                                    "Precio Gasoleo Premium", "Precio Gasolina 95 E10", "Precio Gasolina 95 E5", "Precio Gasolina 95 E5 Premium", "Precio Gasolina 98 E10", "Precio Gasolina 98 E5", "% BioEtanol", "% Éster metílico"]]

            # Sustituimos los valores vacíos por NaN
            precios_df = precios_df.replace("", np.NaN)

            # Insertamos una columna correspondiente a la fecha para poder distinguir entre los precios en distintos días
            precios_df.insert(0, "Fecha", fecha)

            spinner.ok("✅")
            return fecha, precios_df
        except Exception as e:
            spinner.fail("❌")
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
            spinner.ok("✅")
        except Exception as e:
            spinner.fail("❌")
            log.error(f"Error inesperado. {e}")
            sys.exit(0)


def commitActualizacionesPrecios(fecha):
    with yaspin(text="Actualizando repositorio local y remoto con los nuevos cambios") as spinner:
        try:
            repo = Repo(".") # Sitúo el repositorio de git desde donde lanzo el script del proyecto

            # Añado todos los cambios al staging area y hago un commit con los nuevos datos
            repo.git.add(all=True) # git add .
            repo.git.commit('-m', f'Actualizacion de precios para el día: {fecha}') # git commit -m <mensaje>
            # Hacemos push al repositorio remoto
            origin = repo.remote(name='origin')
            origin.push()
            spinner.ok("✅")
        except Exception as e:
            spinner.fail("❌")
            log.error(f"Error inesperado. {e}")
            sys.exit(0)

def registrarDiaActualizacion(fecha):
    # Almacenamos en un fichero la fecha del último día del que se tienen datos del combustible
    with open("data/UltimoDia.txt", "w", encoding="utf-8") as file:
        file.write(fecha)
    
def comprobarYaActualizado(fechaActual):
    # Comprueba si la última fecha de la que se disponen datos del precio es la misma que la actual para evitar duplicidades en los datos
    try:
        with open ("data/UltimoDia.txt", "r", encoding="utf-8") as file:
            fechaActualizacion = file.read()
    except FileNotFoundError:
        return False
    
    if fechaActual == fechaActualizacion:
        return True
    
    return False

if __name__ == "__main__":
    # Obtenemos los datos de los precios y la fecha
    fecha, datosPrecio_df = obtenerDatosPrecios()

    # Comprobamos si existe el fichero de datos para los precios de ese mes para guardar los nuevos datos con cabecera o sin ella
    
    if existeFicheroDatos(fecha=fecha):
        guardarDatos(dataframe=datosPrecio_df, fecha=fecha, esPrimero=False)
    else:
        guardarDatos(dataframe=datosPrecio_df, fecha=fecha, esPrimero=True)

    # Actualizamos el valor de la última fecha de la que disponemos datos    
    registrarDiaActualizacion(fecha) 
    
    # Commiteamos los cambios y los subimos al repositorio remoto
    commitActualizacionesPrecios(fecha)