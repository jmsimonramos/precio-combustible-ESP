import numpy as np
import pandas as pd
from yaspin import yaspin
from src.IO import IO
from git import Repo
from os.path import exists
import sys
import logging as log

class Utils():
    def __init__(self):
        self.config = IO().cargarConfiguracion()

        # Configuramos el log con la ruta del fichero, el modo de uso (a = añadir al final del fichero), el formato del mensaje (tiempo - tipoError - mensaje) y la prioridad mínima(DEBUG = más baja, por lo que cualquier aviso se registrará en el log)
        log.basicConfig(filename=self.config["META"]["LOG_PATH"], filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', datefmt=self.config["META"]["FORMATO_FECHA_LOG"], level=log.DEBUG)

    # Transforma los precios en formato strings con , a formato float
    def formatearPrecio(self, precio):
        if pd.isna(precio):
            return np.nan
        return float(precio.replace(",", "."))

    def commitActualizacionesPrecios(self, fecha):
        with yaspin(text="Actualizando repositorio local y remoto con los nuevos cambios") as spinner:
            try:
                repo = Repo(".") # Sitúo el repositorio de git desde donde lanzo el script del proyecto

                # Añado todos los cambios al staging area y hago un commit con los nuevos datos
                repo.git.add(all=True) # git add .
                repo.git.commit('-m', f'Actualizacion de precios para el día: {fecha}') # git commit -m <mensaje>
                # Hacemos push al repositorio remoto
                origin = repo.remote(name=self.config["META"]["REMOTO"])
                origin.push()
                spinner.ok(self.config["META"]["ICONO_OK"])
            except Exception as e:
                spinner.fail(self.config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)

    def registrarUltimaFechaDisponibleProyecto(self, fecha):
        # Cambiamos el valor del último día de datos en la configuración
        self.config["META"]["ULTIMO_DIA"] = fecha
        IO().guardarConfiguracion(self.config)
    
    def yaTengoLosDatos(self, fechaActual):
        # Comprueba si la última fecha de la que se disponen datos del precio es la misma que la actual para evitar duplicidades en los datos
        return fechaActual == self.config["META"]["ULTIMO_DIA"]
    
    def existeFicheroDatos(self, fecha):
        # Comprobamos si existe el fichero para ese mes. Si existe = NO es primero de mes --> No hay que crear un nuevo archivo
        # Si NO existe = ES primero de mes --> Creamos nuevo archivo
        return exists(f"{self.config['META']['EESS_PATH']}{fecha[3:]}.csv")