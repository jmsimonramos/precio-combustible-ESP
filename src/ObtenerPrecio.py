import pandas as pd
import numpy as np
import requests, sys
import logging as log
from yaspin import yaspin
from src.IO import IO
from src.Utils import Utils

class ObtenerPrecio():
    def __init__(self):
        self.__Utils, self.__IO = Utils(), IO()
        self.__config = self.__IO.cargarConfiguracion()
        self.__fecha = ""
        self.__precios_raw = ""
        self.__preciosEESS, self.__preciosCCAA, self.__preciosProvincia = "", "", ""

        # Configuramos el log con la ruta del fichero, el modo de uso (a = añadir al final del fichero), el formato del mensaje (tiempo - tipoError - mensaje) y la prioridad mínima(DEBUG = más baja, por lo que cualquier aviso se registrará en el log)
        log.basicConfig(filename=self.__config["META"]["LOG_PATH"], filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', datefmt=self.__config["META"]["FORMATO_FECHA_LOG"], level=log.DEBUG)

    def obtenerPrecioCombustible(self):
        self.__obtenerDatosPrecio() # Obtenemos los datos de la web del gobierno
        self.__procesarDatosPrecio() # Procesamos los datos
        with yaspin(text="Calculando precios medios por CCAA y provincias") as spinner:
            try: # Calculamos el precio por Provincia y CCAA
                self.__calcularPrecioCCAA()
                self.__calcularPrecioProvincias()
                spinner.ok(self.__config["META"]["ICONO_OK"])
            except Exception as e:
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)
        # Comprobamos si existe el fichero de datos para los precios de ese mes para guardar los nuevos datos con cabecera o sin ella
        with yaspin(text="Guardando los datos en el .csv") as spinner:
            try:
                self.__guardarDatos()
                spinner.ok(self.__config["META"]["ICONO_OK"])
            except Exception as e:
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)

        # Actualizamos el valor de la última fecha de la que disponemos datos    
        self.__Utils.registrarUltimaFechaDisponibleProyecto(self.__fecha) 
    
    def __guardarDatos(self):
        if self.__Utils.existeFicheroDatos(self.__fecha):
            self.__IO.guardarDataFrame(self.__preciosEESS, self.__fecha, esPrimero=False)
            self.__IO.guardarDataFrame(self.__preciosCCAA, self.__fecha, esPrimero=False, esCCAA=True)
            self.__IO.guardarDataFrame(self.__preciosProvincia, self.__fecha, esPrimero=False, esProvincia=True)
        else:
            self.__IO.guardarDataFrame(self.__preciosEESS, self.__fecha, esPrimero=True)
            self.__IO.guardarDataFrame(self.__preciosCCAA, self.__fecha, esPrimero=True, esCCAA=True)
            self.__IO.guardarDataFrame(self.__preciosProvincia, self.__fecha, esPrimero=True, esProvincia=True)

    def __obtenerDatosPrecio(self):
        with yaspin(text="Obteniendo datos del precio del combustible") as spinner:
            # Realizamos una petición al servicio rest y comprobamos que se ha realizado correctamente (código de estado = 200)
            request = requests.get(self.__config["URL"]["API_URL"])

            if request.status_code != 200:  # Mostramos un error si no se lleva a cabo la petición satisfactoriamente
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Fallo a la hora de realizar la petición. Status Code: {request.status_code}")
                sys.exit(0)

            json_data = request.json() # Formateamos el contenido de la respuesta a JSON
            spinner.ok(self.__config["META"]["ICONO_OK"])
        
        with yaspin(text="Comprobando que los datos no son repetidos") as spinner:
        # Almacenamos por separado los valores correspondientes a la fecha de la petición y al listado de los precios de las estaciones de servicio
            try:
                self.__fecha = json_data["Fecha"].split(" ")[0].replace("/", "-")
                #__fecha = obtener__fechaUltimaModificacionWeb()
                self.__precios_raw = json_data["ListaEESSPrecio"]
            
                # Si dispongo de datos para ese día se para el programa para evitar duplicidades en los datos
                if self.__Utils.yaTengoLosDatos(self.__fecha): 
                    spinner.ok(self.__config["META"]["ICONO_OK"])
                    print(f"👌 Ya se disponen de los datos para la fecha: {self.__fecha}")
                    log.info(f"Ya se disponen de los datos para la fecha: {self.__fecha}")
                    sys.exit(0)
                spinner.ok(self.__config["META"]["ICONO_OK"])

            except Exception as e:
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)

    def __procesarDatosPrecio(self):
        with yaspin(text="Procesando datos") as spinner:
            # Creamos un dataframe con los precios y nos quedamos únicamente con las columnas relativas a los precios del combustible
            try:
                self.__preciosEESS = pd.json_normalize(self.__precios_raw)
                self.__preciosEESS = self.__preciosEESS[self.__config["COMBUSTIBLE"]["COLUMNAS"]]
                # Sustituimos los valores vacíos por NaN
                self.__preciosEESS = self.__preciosEESS.replace("", np.NaN)
                            
                self.__formatearPreciosCombustible()
                
                # Insertamos una columna correspondiente a la fecha para poder distinguir entre los precios en distintos días
                self.__preciosEESS.insert(0, "Fecha", self.__fecha)
                spinner.ok(self.__config["META"]["ICONO_OK"])
            except Exception as e:
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)

    def __formatearPreciosCombustible(self):
        for columna in self.__config["COMBUSTIBLE"]["COLUMNAS_FORMATEAR"]:
            self.__preciosEESS[columna] = self.__preciosEESS[columna].apply(lambda precio: self.__Utils.formatearPrecio(precio))
    
    def __calcularPrecioCCAA(self):
        # Agrupamos los datos por comunidad y calculamos la media
        self.__preciosCCAA = self.__preciosEESS.groupby(["IDCCAA"], as_index=False).mean().round(3)
        # Sustituimos los identificadores de cada Comunidad Autónoma por su valor original
        self.__preciosCCAA = self.__preciosCCAA.replace({"IDCCAA": self.__config["EESS"]["CCAA"]}) 
        # Renombramos la columna para que el título se corresponda con su contenido
        self.__preciosCCAA.rename(columns={"IDCCAA": "CCAA"}, inplace=True)
        # Insertamos el valor de la fecha del día
        self.__preciosCCAA.insert(0, "Fecha", self.__fecha)  
        

    def __calcularPrecioProvincias(self):
        # Agrupamos los datos por provincia y calculamos la media
        self.__preciosProvincia = self.__preciosEESS.groupby(["Provincia"], as_index=False).mean().round(3)
        # Insertamos el valor de la fecha del día
        self.__preciosProvincia.insert(0, "Fecha", self.__fecha)  