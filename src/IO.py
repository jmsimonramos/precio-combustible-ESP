import json
import pandas as pd
import numpy as np

class IO():
    def __init__(self):
        self.config = self.cargarConfiguracion()
        
    # Carga los datos de la configuración fijados en el fichero config.json
    def cargarConfiguracion(self, ruta="config.json"):
        with open(ruta, 'r', encoding='utf-8') as file:
            configuracion = json.load(file)
        return configuracion

    # Guarda la nueva configuración en el fichero config.json
    def guardarConfiguracion(self, configuracion, ruta="config.json"):
        with open (ruta, "w",  encoding="utf-8") as file:
            json.dump(configuracion, file, indent=4)

    def guardarDataFrame(self, dataframe, fecha, esPrimero, esProvincia=False, esCCAA=False):
        # Si el DataFrame contiene los precios del primer día del mes lo guardamos en el fichero con las cabeceras. En caso contrario lo guardamos sin ellas para así ir concatenando los datos de los diferentes días del mes
            if esPrimero: 
                if esProvincia:
                    dataframe.to_csv(f"{self.config['META']['PROVINCIA_PATH']}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=True, index=False)
                elif esCCAA:
                    dataframe.to_csv(f"{self.config['META']['CCAA_PATH']}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=True, index=False)
                else:
                    dataframe.drop(columns=["IDCCAA", "Provincia"], axis=1).to_csv(f"{self.config['META']['EESS_PATH']}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=True, index=False)
            else:
                if esProvincia:
                    dataframe.to_csv(f"{self.config['META']['PROVINCIA_PATH']}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=False, index=False, mode="a")
                elif esCCAA:
                    dataframe.to_csv(f"{self.config['META']['CCAA_PATH']}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=False, index=False, mode="a")
                else:
                    dataframe.to_csv(f"{self.config['META']['EESS_PATH']}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=False, index=False, mode="a")
