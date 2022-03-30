from os.path import exists
import requests
import pandas as pd
import numpy as np
from git import Repo

DATA_PATH = "data/historico/precioEESS-"

def obtenerDatosPrecios():
    print("Realizando petición al servicio REST")
    # Realizamos una petición al servicio rest y comprobamos que se ha realizado correctamente (código de estado = 200)
    request = requests.get(
        "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/")
    print("Petión al servicio REST realizada")

    if request.status_code != 200:  # Mostramos un error si no se lleva a cabo la petición satisfactoriamente
        print("ERROR: Ha ouccrrido un error durante la petición de datos")
        print(f"Código de estado: {request.status_code}")
        exit(0)

    print(f"Código de estado: {request.status_code}")

    json_data = request.json()

    # Almacenamos por separado los valores correspondientes a la fecha de la petición y al listado de los precios de las estaciones de servicio
    fecha = json_data["Fecha"].split(" ")[0].replace("/", "-")
    precios = json_data["ListaEESSPrecio"]
    
    if comprobarYaActualizado(fecha):
        print(f"Ya se disponen de los datos para la fecha: {fecha}. Saliendo...")
        exit(1)

    # Creamos un dataframe con los precios y nos quedamos únicamente con las columnas relativas a los precios del combustible
    precios_df = pd.json_normalize(precios)

    precios_df = precios_df[["IDEESS", "Precio Biodiesel", "Precio Bioetanol", "Precio Gas Natural Comprimido", "Precio Gas Natural Licuado", "Precio Gases licuados del petróleo", "Precio Gasoleo A", "Precio Gasoleo B",
                             "Precio Gasoleo Premium", "Precio Gasolina 95 E10", "Precio Gasolina 95 E5", "Precio Gasolina 95 E5 Premium", "Precio Gasolina 98 E10", "Precio Gasolina 98 E5", "% BioEtanol", "% Éster metílico"]]

    # Sustituimos los valores vacíos por NaN
    precios_df = precios_df.replace("", np.NaN)

    print(
        f"DataFrame de precios generado correctamente!!\nTamaño del DataFrame: {precios_df.shape}")

    # Insertamos una columna correspondiente a la fecha para poder distinguir entre los precios en distintos días
    precios_df.insert(0, "Fecha", fecha)

    return fecha, precios_df


def existeFicheroDatos(fecha):
    # Comprobamos si existe el fichero para ese mes. Si existe = NO es primero de mes --> No hay que crear un nuevo archivo
    # Si NO existe = ES primero de mes --> Creamos nuevo archivo
    return exists(f"{DATA_PATH}{fecha[3:]}.csv")


def guardarDatos(dataframe, fecha, esPrimero):
    if esPrimero:
        print("Guardando datos CON cabeceras")
        dataframe.to_csv(
            f"{DATA_PATH}{fecha[3:]}.csv", sep=";", encoding="utf-8", header=True, index=False)
    else:
        print("Guardando datos SIN cabeceras")
        dataframe.to_csv(f"{DATA_PATH}{fecha[3:]}.csv", sep=";",
                         encoding="utf-8", header=False, index=False, mode="a")

    print("DataFrame Guardado!")


def commitActualizacionesPrecios(fecha):
    repo = Repo(".")
    print(f"El repositorio local es: {repo}")

    repo.git.add(all=True)
    repo.git.commit('-m', f'Actualizacion de precios para el día: {fecha}')

    print("Realizando PUSH a rama remota")
    try:
        origin = repo.remote(name='origin')
        origin.push()
    except Exception:
        pass

def registrarDiaActualizacion(fecha):
    with open("data/UltimoDia.txt", "w", encoding="utf-8") as file:
        file.write(fecha)
    
def comprobarYaActualizado(fecha):
    with open ("data/UltimoDia.txt", "r", encoding="utf-8") as file:
        fechaActualizacion = file.read()
    
    if fecha == fechaActualizacion:
        return True
    
    return False

if __name__ == "__main__":
    fecha, datosPrecio_df = obtenerDatosPrecios()

    if existeFicheroDatos(fecha=fecha):
        guardarDatos(dataframe=datosPrecio_df, fecha=fecha, esPrimero=False)
    else:
        guardarDatos(dataframe=datosPrecio_df, fecha=fecha, esPrimero=True)

    print(f"Extracción de datos del día {fecha} realizada correctamente!!")

    print("Actualizando cambios en el repositorio")
    commitActualizacionesPrecios(fecha)

    registrarDiaActualizacion(fecha)