from src.ObtenerPrecio import ObtenerPrecio
from src.Visualizacion import Visualizacion
from src.Utils import Utils

if __name__ == "__main__":
    # Obtenemos los precios de los combustibles
    obtenerPrecio = ObtenerPrecio()
    obtenerPrecio.obtenerPrecioCombustible()

    # Generamos los gráficos
    Visualizacion().generarVisualizaciones()
    
    # Hacemos un commit con los cambios y los subimos al repositorio remoto
    Utils().commitActualizacionesPrecios()

    # Mostramos la tabla con los tiempos de ejecución
    Utils().mostrarTablaTiemposEjecucion()