import numpy as np
import pandas as pd
from src.IO import IO
from os.path import exists
import time
class Utils():
    def __init__(self):
        self.config = IO().cargarConfiguracion()
    # Transforma los precios en formato strings con , a formato float
    def formatearPrecio(self, precio):
        if pd.isna(precio):
            return np.nan
        return float(precio.replace(",", "."))

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

    def guardarFigura(self, fig, titulo):
        fig.get_figure().savefig(titulo, bbox_inches='tight')
    
    def obtenerTiempo(self):
        return time.time()