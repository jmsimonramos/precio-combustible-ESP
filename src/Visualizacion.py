import pandas as pd
import os, sys
import plotly.express as px
import plotly.graph_objects as go
import plotly as plo
import unidecode
import geopandas as gpd
import datetime
from dateutil import relativedelta
from src.IO import IO
from src.Utils import Utils

class Visualizacion():
    def __init__(self):
        self.__Utils, self.__IO = Utils(), IO()
        self.__config = self.__IO.cargarConfiguracion()
        self.__dfCCAA = pd.DataFrame()
        self.__dfProvincia = pd.DataFrame()
        self.__EESS = pd.DataFrame()
        self.__dfHistorico = pd.DataFrame()
        self.__mapaCCAA = pd.DataFrame()
        self.__mapaProvincia = pd.DataFrame()
        self.__fechas = []

    def generarVisualizaciones(self):
        print("Cargando datos para la visualización")
        try:
            self.__cargarDatosCCAA() # Cargamos los datos de los precios por CCAA
            self.__cargarDatosProvincia() # Cargamos los datos de los precios por Provincias
            self.__cargarDatosMapa() # Cargamos los datos del mapa
        except Exception as e:
            print(e)
            sys.exit(0)
    
        print("Generando gráficas")
        try:
            self.__generarGraficos() # Genera todos los gráficos
        except Exception as e:
            print(e)
            print(f"Error inesperado. {e}")
            sys.exit(0)
        self.__IO.guardarConfiguracion(self.__config)
    
    def __cargarDatosMapa(self):
        self.__mapaCCAA = self.__dfCCAA.groupby(["Fecha", "CCAA"], as_index=False).mean().round(3)
        self.__mapaCCAA = self.__mapaCCAA[self.__mapaCCAA["Fecha"] == self.__config["META"]["ULTIMO_DIA"]].drop(columns=["Fecha"])

        self.__mapaCCAA = gpd.GeoDataFrame.from_file(f"{self.__config['VISUALIZACION']['RUTA_MAPA']}CCAA.json").merge(self.__mapaCCAA, on="CCAA").drop(columns=["id"]).set_index("CCAA")

        # DATOS MAPA PROVINCIAS

        self.__mapaProvincia = self.__dfProvincia.groupby(["Fecha", "Provincia"], as_index=False).mean().round(3)#
        self.__mapaProvincia = self.__mapaProvincia[self.__mapaProvincia["Fecha"] == self.__config["META"]["ULTIMO_DIA"]].drop(columns=["Fecha"])

        self.__mapaProvincia = gpd.GeoDataFrame.from_file(f"{self.__config['VISUALIZACION']['RUTA_MAPA']}PROVINCIAS.json").merge(self.__mapaProvincia, on="Provincia").drop(columns=["id"]).set_index("Provincia")

    def __cargarDatosCCAA(self):
        # Obtenemos todos los ficheros de todos los meses disponibles para las CCAA
        lista_precios_ccaa = sorted([file for file in os.listdir(self.__config["VISUALIZACION"]["RUTA_CCAA"])]) #
        
        # Cargamos los datos de cada fichero y los concatenamos para generar un dataset con todo el histórico
        for fichero in lista_precios_ccaa:
            df_aux = pd.read_csv(f"{self.__config['VISUALIZACION']['RUTA_CCAA']}{fichero}", sep=";", encoding="utf-8")
            self.__dfCCAA = pd.concat([self.__dfCCAA, df_aux], axis=0) # Concatenamos los datasets de manera horizontal

        self.__dfHistorico = self.__dfCCAA.groupby(["Fecha"], as_index=False).mean().round(3) # Utilizamos el dataset de las CCAA para obtener el valor medio del combustible a nivel nacional

        # Al ser un dataframe generado mediante agrupación, ordenamos por fecha ya que de lo contrario aparecerían los registros desordenados
        self.__dfHistorico["Fecha"] = pd.to_datetime(self.__dfHistorico["Fecha"], format="%d-%m-%Y")
        self.__dfHistorico.sort_values(by="Fecha", ascending=True, inplace=True)
        self.__dfHistorico["Fecha"] = self.__dfHistorico["Fecha"].dt.strftime('%d-%m-%Y')

        # Renombramos las columnas para eliminar ruido en los gráficos
        self.__dfHistorico.columns = self.__dfHistorico.columns.str.replace("Precio", "")
        self.__dfCCAA.columns = self.__dfCCAA.columns.str.replace("Precio", "")
        
        # Obtenemos el lsitado de las fechas para las que disponemos de datos y lo pasamos a formato lista eliminando los valores intermedios para tener únicamente la primera fecha disponible y la última. Esto nos servirá posteriormente para mejorar los datos en las visualizaciones
        self.__fechas = self.__dfCCAA.Fecha.unique()
        self.__fechas[1:-1] = ["" for _ in self.__fechas[1:-1]]

    def __cargarDatosProvincia(self):
        # Obtenemos todos los ficheros de todos los meses disponibles para las Provincias
        lista_precios_provincia = sorted([file for file in os.listdir(self.__config["VISUALIZACION"]["RUTA_PROVINCIA"])])
        
        # Cargamos los datos de cada fichero y los concatenamos para generar un dataset con todo el histórico
        for fichero in lista_precios_provincia:
            df_aux = pd.read_csv(f"{self.__config['VISUALIZACION']['RUTA_PROVINCIA']}{fichero}", sep=";", encoding="utf-8")
            self.__dfProvincia = pd.concat([self.__dfProvincia, df_aux], axis=0) # Concatenamos los datasets de manera horizontal
        
        self.__dfProvincia.columns = self.__dfProvincia.columns.str.replace("Precio", "")
        
    def __generarGraficos(self):
        # Generamos gráficos de líneas de forma dinámica para cada combustible fijado en la configuración
        self.__generarGraficoEvolucionPrecioNacional()
        self.__generarGraficosGenerales()
        self.__generarGraficosMapa()
        self.__generarGraficosCCAA()
        self.__generarGraficosProvincias()
        self.__generarHistogramaEESS()

    def __generarGraficosMapa(self):
        # CCAA
        for combustible in self.__dfCCAA.columns[2:-2]:
            fig = px.choropleth_mapbox(
                self.__mapaCCAA,
                geojson=self.__mapaCCAA.geometry,
                locations=self.__mapaCCAA.index,
                color=combustible,
                center={"lat": 40.4165, "lon": -3.70256},
                mapbox_style="open-street-map",
                zoom=self.__config["VISUALIZACION"]["ZOOM"],
                color_continuous_scale= self.__config["VISUALIZACION"]["PALETA"],
                title = f"Mapa de Comunidades Autónomas con la media del<br> {combustible} de hoy ({self.__config['META']['ULTIMO_DIA']})",
                width = self.__config["VISUALIZACION"]["ANCHO"]
            )
            plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_MAPA']}CCAA-{unidecode.unidecode(combustible.replace(' ', ''))}.html", include_plotlyjs=False, full_html=False)

        # PROVINCIAS
        for combustible in self.__dfProvincia.columns[2:-2]:
            fig = px.choropleth_mapbox(
                self.__mapaProvincia,
                geojson=self.__mapaProvincia.geometry,
                locations=self.__mapaProvincia.index,
                color=combustible,
                center={"lat": 40.4165, "lon": -3.70256},
                mapbox_style="open-street-map",
                zoom=self.__config["VISUALIZACION"]["ZOOM"],
                color_continuous_scale= self.__config["VISUALIZACION"]["PALETA"],
                title = f"Mapa de Provincias con la media del<br> {combustible} de hoy ({self.__config['META']['ULTIMO_DIA']})",
                width = self.__config["VISUALIZACION"]["ANCHO"]
            )
            plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_MAPA']}PROVINCIA-{unidecode.unidecode(combustible.replace(' ', ''))}.html", include_plotlyjs=False, full_html=False)

    def __calcularPreciosAnteriores(self, num_dias = 0, mesAnterior = False, num_meses = 1):
        hoy = datetime.datetime.strptime(self.__config["META"]["ULTIMO_DIA"], '%d-%m-%Y').date()
        if mesAnterior:
            # Obtenemos el mismo día que el que estamos comparando pero para el mes anterior
            fechaAnterior = hoy - relativedelta.relativedelta(months = num_meses)
        else:
            fechaAnterior = hoy - datetime.timedelta(days = num_dias)
        
        fechaAnterior = fechaAnterior.strftime('%d-%m-%Y')
        return self.__dfHistorico[self.__dfHistorico["Fecha"] == fechaAnterior][self.__dfHistorico.columns[:-2]]

    def __generarGraficoEvolucionPrecioNacional(self):
        fig = go.Figure()
        for combustible in self.__dfHistorico.columns[1:-2]:
            fig.add_trace(go.Scatter(
                x = self.__dfHistorico["Fecha"],
                y = self.__dfHistorico[combustible],
                name = combustible.replace("Precio", ""),
                mode = "lines+markers",
                hovertemplate="%{y}€"
            ))
        fig.update_layout(
            title="Evolución del precio medio del combustible en España",
            xaxis_title="Fecha",
            yaxis_title="Precio (€)",
            legend_title="Combustible",
            hovermode="x unified",
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            xaxis = dict(
                tickmode = "array",
                tickvals = self.__fechas,
                ticktext = self.__fechas
            )
        )

        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}evolucionPrecio.html", include_plotlyjs=False, full_html=False)

    def __generarGraficosGenerales(self):
        
        datosHoy = self.__dfHistorico[self.__dfHistorico["Fecha"] == self.__config["META"]["ULTIMO_DIA"]][self.__dfHistorico.columns[:-2]]
        datosSemanaPasada = self.__calcularPreciosAnteriores(num_dias = 7)

        fig = go.Figure(data=[
            go.Bar(
                name = f"Semana Pasada {datosSemanaPasada.head(1)['Fecha'].values[0]}",
                x = datosSemanaPasada.head(1).columns[1:].values,
                y = datosSemanaPasada.head(1).iloc[:, 1:].values[0],
                text = datosSemanaPasada.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                marker_color="#646def",
                hovertemplate="%{y}€",
            ),
            go.Bar(
                name = f"Hoy {datosHoy.head(1)['Fecha'].values[0]}",
                x = datosHoy.head(1).columns[1:].values,
                y = datosHoy.head(1).iloc[:, 1:].values[0],
                text = datosHoy.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                marker_color="#de5f46",
                hovertemplate="%{y}€",
            )
        ])
        fig.update_layout(
            title="Comparativa precios combustible entre el día actual y la semana pasada",
            xaxis_title="Tipo de Combustible",
            yaxis_title="Precio (€)",
            legend_title="Día",
            hovermode="x unified",
            barmode='group',
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}comparativaPrecioSemanaPasada.html", include_plotlyjs=False, full_html=False)

        # Calculamos los meses anteriores para los meses de los que disponemos de datos
        añoActual = self.__config["META"]["ULTIMO_DIA"].split("-")[-1]

        mesesAnteriores = len([file for file in os.listdir(self.__config["VISUALIZACION"]["RUTA_CCAA"]) if f"-{añoActual}" in file]) - 1
        
        fig = go.Figure()
        for indice, mes in enumerate( range(mesesAnteriores, 0, -1) ) :
            datosAnteriores = self.__calcularPreciosAnteriores(mesAnterior=True, num_meses=mes)
            fig.add_trace(go.Bar(
                name = f"Hace {mes} meses ({datosAnteriores.head(1)['Fecha'].values[0]})",
                x = datosAnteriores.head(1).columns[1:].values,
                y = datosAnteriores.head(1).iloc[:, 1:].values[0],
                text = datosAnteriores.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                marker_color = self.__config["VISUALIZACION"]["COLORES"][indice],
                hovertemplate="%{y}€",
            ))
        
        fig.add_trace(go.Bar(
            name = f"Hoy ({datosHoy.head(1)['Fecha'].values[0]})",
            x = datosHoy.head(1).columns[1:].values,
            y = datosHoy.head(1).iloc[:, 1:].values[0],
            text = datosHoy.head(1).iloc[:, 1:].values[0],
            textposition = 'auto',
            marker_color="#de5f46",
            hovertemplate="%{y}€",
        ))

        fig.update_layout(
            title="Comparativa precios del combustible en los últimos meses",
            xaxis_title="Tipo de Combustible",
            yaxis_title="Precio (€)",
            legend_title="Meses",
            hovermode="x unified",
            barmode='group',
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}comparativaPrecioMeses.html", include_plotlyjs=False, full_html=False)

    def __generarGraficosCCAA(self):
        # COMPARATIVA CCAA
        fig = go.Figure()
        for ccaa in self.__dfCCAA.CCAA.unique():
            datos = self.__dfCCAA[self.__dfCCAA["CCAA"] == ccaa]
            for combustible in self.__dfCCAA.columns[2:-2]:
                fig.add_trace(
                    go.Scatter(
                        x = datos["Fecha"],
                        y = datos[combustible],
                        name = f"{combustible.replace('Precio', '')}-{ccaa}",
                        visible = "legendonly",
                        mode = "lines+markers",
                        hovertemplate="%{y}€",
                    )
            )

        fig.update_layout(
            title="Evolución de los precios del combustible por Comunidad Autónoma. (Clicar en la leyenda los valores que se quieran visualizar en el gráfico)",
            xaxis_title="Fecha",
            yaxis_title="Precio (€)",
            legend_title="Combustible + CCAA",
            hovermode="x unified",
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            xaxis = dict(
                tickmode = "array",
                tickvals = self.__fechas,
                ticktext = self.__fechas
            )
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_CCAA']}comparativaPrecios.html", include_plotlyjs=False, full_html=False)
    
    def __generarHistogramaEESS(self):
        ruta = self.__config["VISUALIZACION"]["RUTA_EESS"]
        fichero_datos = sorted([f"{ruta}{fichero}" for fichero in os.listdir(ruta)], key = os.path.getmtime, reverse=True)[0]
        
        self.__EESS = pd.read_csv(fichero_datos, sep=";", encoding="utf-8")
        self.__EESS = self.__EESS[self.__EESS["Fecha"] == self.__config["META"]["ULTIMO_DIA"]]

        fig = go.Figure()

        for combustible in self.__EESS.columns[2:-2]:
            fig.add_trace(go.Histogram(
                x = self.__EESS[combustible],
                name = combustible.replace("Precio", ""),
                hovertemplate="%{y}"
            ))

        fig.update_layout(
                    title=f"Distribución del precio de los combustibles en las estaciones de servicio para el día: {self.__config['META']['ULTIMO_DIA']}",
                    xaxis_title="Precio (€)",
                    yaxis_title="Total",
                    barmode="overlay",
                    legend_title="Combustible",
                    hovermode="x unified",
                )
        fig.update_traces(opacity=0.75)
        
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_EESS']}histogramaPrecios.html", include_plotlyjs=False, full_html=False)

    def __generarGraficosProvincias(self):
        # COMPARATIVA PROVINCIAS
        fig = go.Figure()
        for provincia in self.__dfProvincia.Provincia.unique():
            datos = self.__dfProvincia[self.__dfProvincia["Provincia"] == provincia]
            for combustible in self.__dfProvincia.columns[2:-2]:
                fig.add_trace(
                    go.Scatter(
                        x = datos["Fecha"],
                        y = datos[combustible],
                        name = f"{combustible.replace('Precio', '')}-{provincia}",
                        visible = "legendonly",
                        mode = "lines+markers",
                        hovertemplate="%{y}€",
                    )
            )
        fig.update_layout(
            title="Evolución de los precios del combustible por Provincia. (Clicar en la leyenda los valores que se quieran visualizar en el gráfico)",
            xaxis_title="Fecha",
            yaxis_title="Precio (€)",
            legend_title="Combustible + Provincia",
            hovermode="x unified",
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            xaxis = dict(
                tickmode = "array",
                tickvals = self.__fechas,
                ticktext = self.__fechas
            )
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_PROVINCIA']}comparativaPrecios.html", include_plotlyjs=False, full_html=False)