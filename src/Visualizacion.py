import pandas as pd
import os, sys
from src.Utils import Utils
from src.IO import IO
from yaspin import yaspin
import logging as log
import plotly.express as px
import plotly.graph_objects as go
import plotly as plo
import unidecode
import geopandas as gpd

class Visualizacion():
    def __init__(self):
        self.__Utils = Utils()
        self.__config = IO().cargarConfiguracion()
        self.__dfCCAA = pd.DataFrame()
        self.__dfProvincia = pd.DataFrame()
        self.__dfHistorico = pd.DataFrame()
        self.__mapaCCAA = pd.DataFrame()
        self.__mapaProvincia = pd.DataFrame()

        # Configuramos el log con la ruta del fichero, el modo de uso (a = añadir al final del fichero), el formato del mensaje (tiempo - tipoError - mensaje) y la prioridad mínima(DEBUG = más baja, por lo que cualquier aviso se registrará en el log)
        log.basicConfig(filename=self.__config["META"]["LOG_PATH"], filemode="a", format='%(asctime)s - %(levelname)s - %(message)s', datefmt=self.__config["META"]["FORMATO_FECHA_LOG"], level=log.DEBUG)
        
    
    def generarVisualizaciones(self):
        with yaspin(text="Cargando datos para la visualización") as spinner:
            try:
                self.__cargarDatosCCAA() # Cargamos los datos de los precios por CCAA
                self.__cargarDatosProvincia() # Cargamos los datos de los precios por Provincias
                self.__cargarDatosMapa() # Cargamos los datos del mapa
                spinner.ok(self.__config["META"]["ICONO_OK"])
            except Exception as e:
                print(e)
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)
        
        with yaspin(text="Generando gráficas") as spinner:
            try:
                self.__generarGraficos() # Genera todos los gráficos
                spinner.ok(self.__config["META"]["ICONO_OK"])
            except Exception as e:
                print(e)
                spinner.fail(self.__config["META"]["ICONO_ERROR"])
                log.error(f"Error inesperado. {e}")
                sys.exit(0)
    
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

    
    def __cargarDatosProvincia(self):
        # Obtenemos todos los ficheros de todos los meses disponibles para las Provincias
        lista_precios_provincia = sorted([file for file in os.listdir(self.__config["VISUALIZACION"]["RUTA_PROVINCIA"])])
        
        # Cargamos los datos de cada fichero y los concatenamos para generar un dataset con todo el histórico
        for fichero in lista_precios_provincia:
            df_aux = pd.read_csv(f"{self.__config['VISUALIZACION']['RUTA_PROVINCIA']}{fichero}", sep=";", encoding="utf-8")
            self.__dfProvincia = pd.concat([self.__dfProvincia, df_aux], axis=0) # Concatenamos los datasets de manera horizontal
        
    def __generarGraficos(self):
        # Generamos gráficos de líneas de forma dinámica para cada combustible fijado en la configuración
        self.__generarGraficosGenerales()
        self.__generarGraficosMapa()
        self.__generarGraficosCCAA()
        self.__generarGraficosProvincias()

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

    def __generarGraficosGenerales(self):
        fig = go.Figure()
        for combustible in self.__dfHistorico.columns[1:-2]:
            fig.add_trace(go.Scatter(
                x = self.__dfHistorico["Fecha"],
                y = self.__dfHistorico[combustible],
                name = f"{combustible}",
                hovertemplate="<br>".join([
                "Fecha: %{x}",
                "Precio (€): %{y}",
                ])
            ))
        fig.update_layout(
            title="Evolución del precio medio del combustible en España",
            xaxis_title="Fecha",
            yaxis_title="Precio (€)",
            legend_title="Combustible",
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}evolucionPrecio.html", include_plotlyjs=False, full_html=False)

        datos = self.__dfHistorico.tail(2)[self.__dfHistorico.columns[:-2]]
        fig = go.Figure(data=[
            go.Bar(
                name = f"Ayer {datos.head(1)['Fecha'].values[0]}",
                x = datos.head(1).columns[1:].values,
                y = datos.head(1).iloc[:, 1:].values[0],
                text = datos.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                hovertemplate="<br>".join([
                    "Combustible: %{x}",
                    "Precio (€): %{y}",
                ])
            ),
            go.Bar(
                name = f"Hoy {datos.tail(1)['Fecha'].values[0]}",
                x = datos.tail(1).columns[1:].values,
                y = datos.tail(1).iloc[:, 1:].values[0],
                text = datos.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                hovertemplate="<br>".join([
                    "Combustible: %{x}",
                    "Precio (€): %{y}",
                ])
            )

        ])
        fig.update_layout(
            title="Comparativa precios combustible últimos días",
            xaxis_title="Tipo de Combustible",
            yaxis_title="Precio (€)",
            legend_title="Día",
            barmode='group',
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}comparativaPrecio.html", include_plotlyjs=False, full_html=False)
        
    def __generarGraficosCCAA(self):
        for combustible in self.__dfCCAA.columns[2:-2]:
            fig = px.line(self.__dfCCAA, x='Fecha', y=combustible, color='CCAA', markers=True, title=f"Evolución del precio del {combustible.replace('Precio ', '')} por Comunidad Autónoma")
            
            plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_CCAA']}evolucion{unidecode.unidecode(combustible.replace(' ', ''))}.html", include_plotlyjs=False, full_html=False)

        # COMPARATIVA CCAA
        fig = go.Figure()
        for ccaa in self.__dfCCAA.CCAA.unique():
            datos = self.__dfCCAA[self.__dfCCAA["CCAA"] == ccaa]
            for combustible in self.__dfCCAA.columns[2:-2]:
                fig.add_trace(
                    go.Scatter(
                        x = datos["Fecha"],
                        y = datos[combustible],
                        name = f"{combustible}-{ccaa}",
                        visible = "legendonly",
                        hovertemplate="<br>".join([
                        "Fecha: %{x}",
                        "Precio (€): %{y}",
                        ])
                    )
            )

        fig.update_layout(
            title="Comparativa precios por Comunidad Autónoma",
            xaxis_title="Fecha",
            yaxis_title="Precio (€)",
            legend_title="Combustible + CCAA",
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_CCAA']}comparativaPrecios.html", include_plotlyjs=False, full_html=False)
    
    def __generarGraficosProvincias(self):
        for combustible in self.__dfProvincia.columns[2:-2]:
            fig = px.line(self.__dfProvincia, x='Fecha', y=combustible, color='Provincia', markers=True, title=f"Evolución del precio del {combustible.replace('Precio ', '')} por Provincias")
            
            plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_PROVINCIA']}evolucion{unidecode.unidecode(combustible.replace(' ', ''))}.html", include_plotlyjs=False, full_html=False)
        
        # COMPARATIVA PROVINCIAS
        fig = go.Figure()
        for provincia in self.__dfProvincia.Provincia.unique():
            datos = self.__dfProvincia[self.__dfProvincia["Provincia"] == provincia]
            for combustible in self.__dfProvincia.columns[2:-2]:
                fig.add_trace(
                    go.Scatter(
                        x = datos["Fecha"],
                        y = datos[combustible],
                        name = f"{combustible}-{provincia}",
                        visible = "legendonly",
                        hovertemplate="<br>".join([
                        "Fecha: %{x}",
                        "Precio (€): %{y}",
                        ])
                    )
            )
        fig.update_layout(
            title="Comparativa precios del combustible por Provincia",
            xaxis_title="Fecha",
            yaxis_title="Precio (€)",
            legend_title="Combustible + Provincia",
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_PROVINCIA']}comparativaPrecios.html", include_plotlyjs=False, full_html=False)