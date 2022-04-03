from unittest import expectedFailure
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys
from src.Utils import Utils
from src.IO import IO
from yaspin import yaspin
import logging as log
class Visualizacion():
    def __init__(self):
        self.__Utils = Utils()
        self.__config = IO().cargarConfiguracion()
        self.__df_MedioCCAA = pd.DataFrame()
        self.__df_MedioProvincia = pd.DataFrame()

        # Configuramos el log con la ruta del fichero, el modo de uso (a = añadir al final del fichero), el formato del mensaje (tiempo - tipoError - mensaje) y la prioridad mínima(DEBUG = más baja, por lo que cualquier aviso se registrará en el log)
        log.basicConfig(filename=self.__config["META"]["LOG_PATH"], filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', datefmt=self.__config["META"]["FORMATO_FECHA_LOG"], level=log.DEBUG)
        # Configuramos parámetros para la generación de los gráficos        
        sns.set_context({"figure.figsize": (16,9)}) # Tamaño figura
        sns.set(style="whitegrid", rc={"lines.linewidth": 2}) # Grosor líneas
    
    def generarVisualizaciones(self):
        with yaspin(text="Cargando datos para la visualización") as spinner:
            try:
                self.__cargarDatosCCAA()
                self.__cargarDatosProvincia()
                spinner.ok(self.__config["META"]["ICONO_OK"])
            except Exception as e:
                print(e)
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)
        
        with yaspin(text="Generando gráficas") as spinner:
            try:
                self.__generarGraficos()
                spinner.ok(self.__config["META"]["ICONO_OK"])
            except Exception as e:
                print(e)
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)
    
    def __cargarDatosCCAA(self):
        lista_precios_ccaa = sorted([file for file in os.listdir(self.__config["VISUALIZACION"]["RUTA_CCAA"])])
        df_CCAA = pd.DataFrame()
        for fichero in lista_precios_ccaa:
            df_aux = pd.read_csv(f"{self.__config['VISUALIZACION']['RUTA_CCAA']}{fichero}", sep=";", encoding="utf-8")
            df_CCAA = pd.concat([df_CCAA, df_aux], axis=0)

        self.__df_MedioCCAA = df_CCAA.groupby(["Fecha", "CCAA"], as_index=False).mean().round(3)
    
    def __cargarDatosProvincia(self):
        lista_precios_provincia = sorted([file for file in os.listdir(self.__config["VISUALIZACION"]["RUTA_PROVINCIA"])])
        df_Provincia = pd.DataFrame()
        for fichero in lista_precios_provincia:
            df_aux = pd.read_csv(f"{self.__config['VISUALIZACION']['RUTA_PROVINCIA']}{fichero}", sep=";", encoding="utf-8")
            df_Provincia = pd.concat([df_Provincia, df_aux], axis=0)

        self.__df_MedioProvincia = df_Provincia.groupby(["Fecha", "Provincia"], as_index=False).mean().round(3)
    
    def __generarGraficos(self):
        for variable in self.__config["VISUALIZACION"]["COMBUSTIBLES_MOSTRAR"]:
            fig = sns.lineplot(x="Fecha", y = variable, data=self.__df_MedioCCAA, hue="CCAA", palette=self.__config["VISUALIZACION"]["PALETA"])
            
            sns.scatterplot(x="Fecha", y = variable, data=self.__df_MedioCCAA, hue="CCAA", legend=False, palette=self.__config["VISUALIZACION"]["PALETA"])

            plt.title(f"Evolución del precio del {variable} por Comunidades Autónomas", fontdict={"fontsize": 19, "fontweight": "bold"})
            plt.legend(title = "CCAA", bbox_to_anchor=(1, 1.05))
            self.__Utils.guardarFigura(fig, f'{self.__config["VISUALIZACION"]["RUTA_GRAFICO"]}CCAA-{variable.replace(" ","")}.png')
            plt.clf()
                        
            # PROVINCIAS
            fig = sns.lineplot(x="Fecha", y = variable, data=self.__df_MedioProvincia, hue="Provincia")
            
            sns.scatterplot(x="Fecha", y = variable, data=self.__df_MedioProvincia, hue="Provincia", legend=False)

            plt.title(f"Evolución del precio del {variable} por Provincias", fontdict={"fontsize": 19, "fontweight": "bold"})
            plt.legend(title = "PROVINCIAS", bbox_to_anchor=(1, 1.05))
            self.__Utils.guardarFigura(fig, f'{self.__config["VISUALIZACION"]["RUTA_GRAFICO"]}PROVINCIAS-{variable.replace(" ","")}.png')
            plt.clf()