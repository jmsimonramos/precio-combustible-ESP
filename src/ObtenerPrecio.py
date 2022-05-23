import pandas as pd
import numpy as np
import requests, sys
from src.IO import IO
from src.Utils import Utils

class ObtenerPrecio():
    def __init__(self):
        self.__Utils, self.__IO = Utils(), IO()
        self.__config = self.__IO.cargarConfiguracion()
        self.__fecha = ""
        self.__precios_raw = ""
        self.__preciosEESS, self.__preciosCCAA, self.__preciosProvincia = "", "", ""

    def obtenerPrecioCombustible(self):
        # Calculamos el tiempo que tarda el proceso de "obtener los datos del precio"
        tiempo_inicial = self.__Utils.obtenerTiempo()
        self.__obtenerDatosPrecio() # Obtenemos los datos de la web del gobierno
        self.__config["RENDIMIENTO"]["TIEMPO_EJECUCION"]["Obtención de datos"] = round(self.__Utils.obtenerTiempo() - tiempo_inicial, 3)

        # Calculamos el tiempo que tarda el proceso de "procesar los datos"
        tiempo_inicial = self.__Utils.obtenerTiempo()
        self.__procesarDatosPrecio() # Procesamos los datos
        self.__config["RENDIMIENTO"]["TIEMPO_EJECUCION"]["Procesar datos combustible"] = round(self.__Utils.obtenerTiempo() - tiempo_inicial, 3)

        print("Calculando precios medios por CCAA y provincias")
        try: # Calculamos el precio por Provincia y CCAA
            # Calculamos el tiempo que tarda el proceso de "calcular precios por CCAA y provincias"
            tiempo_inicial = self.__Utils.obtenerTiempo()
            self.__calcularPrecioCCAA()
            self.__config["RENDIMIENTO"]["TIEMPO_EJECUCION"]["Calcular precio CCAA"] = round(self.__Utils.obtenerTiempo() - tiempo_inicial, 3)

            tiempo_inicial = self.__Utils.obtenerTiempo()
            self.__calcularPrecioProvincias()
            self.__config["RENDIMIENTO"]["TIEMPO_EJECUCION"]["Calcular precio Provincias"] = round(self.__Utils.obtenerTiempo() - tiempo_inicial, 3)
    
        except Exception as e:
            print(f"Error inesperado. {e}")
            sys.exit(0)
        # Comprobamos si existe el fichero de datos para los precios de ese mes para guardar los nuevos datos con cabecera o sin ella
        print("Guardando los datos en el .csv")
        try:
            # Calculamos el tiempo que tarda el proceso de "exportar datos a csv"
            tiempo_inicial = self.__Utils.obtenerTiempo()
            self.__guardarDatos()
            self.__config["RENDIMIENTO"]["TIEMPO_EJECUCION"]["Exportar .csv"] = round(self.__Utils.obtenerTiempo() - tiempo_inicial, 3)

        except Exception as e:            
            print(f"Error inesperado. {e}")
            sys.exit(0)

        # Actualizamos el valor de la última fecha de la que disponemos datos y guardamos la configuración actualizada
        self.__config["META"]["ULTIMO_DIA"] = self.__fecha   
        self.__IO.guardarConfiguracion(self.__config)
    
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
        print("Obteniendo datos del precio del combustible")
        # Realizamos una petición al servicio rest y comprobamos que se ha realizado correctamente (código de estado = 200)
        request = requests.get(self.__config["URL"]["API_URL"])

        if request.status_code != 200:  # Mostramos un error si no se lleva a cabo la petición satisfactoriamente
            print(f"Fallo a la hora de realizar la petición. Status Code: {request.status_code}")
            sys.exit(0)

        json_data = request.json() # Formateamos el contenido de la respuesta a JSON
    
        print("Comprobando que los datos no son repetidos")
        # Almacenamos por separado los valores correspondientes a la fecha de la petición y al listado de los precios de las estaciones de servicio
        try:
            self.__fecha = json_data["Fecha"].split(" ")[0].replace("/", "-")
            #__fecha = obtener__fechaUltimaModificacionWeb()
            self.__precios_raw = json_data["ListaEESSPrecio"]
        
            # Si dispongo de datos para ese día se para el programa para evitar duplicidades en los datos
            if self.__Utils.yaTengoLosDatos(self.__fecha): 
                print(f"👌 Ya se disponen de los datos para la fecha: {self.__fecha}")
                sys.exit(0)

        except Exception as e:
            print.error(f"Error inesperado. {e}")
            sys.exit(0)

    def __procesarDatosPrecio(self):
        print("Procesando datos")
        # Creamos un dataframe con los precios y nos quedamos únicamente con las columnas relativas a los precios del combustible
        try:
            self.__preciosEESS = pd.json_normalize(self.__precios_raw)
            self.__preciosEESS = self.__preciosEESS[self.__config["COMBUSTIBLE"]["COLUMNAS"]]
            # Sustituimos los valores vacíos por NaN
            self.__preciosEESS = self.__preciosEESS.replace("", np.NaN)
                        
            self.__formatearPreciosCombustible()
            
            # Insertamos una columna correspondiente a la fecha para poder distinguir entre los precios en distintos días
            self.__preciosEESS.insert(0, "Fecha", self.__fecha)
        except Exception as e:
            print(f"Error inesperado. {e}")
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