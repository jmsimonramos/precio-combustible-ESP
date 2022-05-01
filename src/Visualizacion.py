import pandas as pd
import os, sys
from src.IO import IO
from yaspin import yaspin
import logging as log
import plotly.express as px
import plotly.graph_objects as go
import plotly as plo
import unidecode
import geopandas as gpd
import datetime
from dateutil import relativedelta

class Visualizacion():
    def __init__(self):
        self.__config = IO().cargarConfiguracion()
        self.__dfCCAA = pd.DataFrame()
        self.__dfProvincia = pd.DataFrame()
        self.__dfHistorico = pd.DataFrame()
        self.__mapaCCAA = pd.DataFrame()
        self.__mapaProvincia = pd.DataFrame()
        self.__fechas = []

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

        # Al ser un dataframe generado mediante agrupación, ordenamos por fecha ya que de lo contrario aparecerían los registros desordenados
        self.__dfHistorico["Fecha"] = pd.to_datetime(self.__dfHistorico["Fecha"], format="%d-%m-%Y")
        self.__dfHistorico.sort_values(by="Fecha", ascending=True, inplace=True)
        self.__dfHistorico["Fecha"] = self.__dfHistorico["Fecha"].dt.strftime('%d-%m-%Y')
        
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

    def __calcularPreciosAnteriores(self, num_dias = 0, mesAnterior = False):
        hoy = datetime.datetime.strptime(self.__config["META"]["ULTIMO_DIA"], '%d-%m-%Y').date()
        if mesAnterior:
            # Obtenemos el mismo día que el que estamos comparando pero para el mes anterior
            fechaAnterior = hoy - relativedelta.relativedelta(months = 1)
        else:
            fechaAnterior = hoy - datetime.timedelta(days = num_dias)
        
        fechaAnterior = fechaAnterior.strftime('%d-%m-%Y')
        return self.__dfHistorico[self.__dfHistorico["Fecha"] == fechaAnterior][self.__dfHistorico.columns[:-2]]

    def __generarGraficosGenerales(self):
        fig = go.Figure()
        for combustible in self.__dfHistorico.columns[1:-2]:
            fig.add_trace(go.Scatter(
                x = self.__dfHistorico["Fecha"],
                y = self.__dfHistorico[combustible],
                name = f"{combustible}",
                mode = "lines+markers",
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
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            xaxis = dict(
                tickmode = "array",
                tickvals = self.__fechas,
                ticktext = self.__fechas
            )
        )

        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}evolucionPrecio.html", include_plotlyjs=False, full_html=False)

        datosHoy = self.__dfHistorico[self.__dfHistorico["Fecha"] == self.__config["META"]["ULTIMO_DIA"]][self.__dfHistorico.columns[:-2]]
        datosSemanaPasada = self.__calcularPreciosAnteriores(num_dias = 7)
        datosMesPasado = self.__calcularPreciosAnteriores(mesAnterior = True)

        fig = go.Figure(data=[
            go.Bar(
                name = f"Semana Pasada {datosSemanaPasada.head(1)['Fecha'].values[0]}",
                x = datosSemanaPasada.head(1).columns[1:].values,
                y = datosSemanaPasada.head(1).iloc[:, 1:].values[0],
                text = datosSemanaPasada.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                hovertemplate="<br>".join([
                    "Combustible: %{x}",
                    "Precio (€): %{y}",
                ])
            ),
            go.Bar(
                name = f"Hoy {datosHoy.head(1)['Fecha'].values[0]}",
                x = datosHoy.head(1).columns[1:].values,
                y = datosHoy.head(1).iloc[:, 1:].values[0],
                text = datosHoy.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                hovertemplate="<br>".join([
                    "Combustible: %{x}",
                    "Precio (€): %{y}",
                ])
            )
        ])
        fig.update_layout(
            title="Comparativa precios combustible entre el día actual y la semana pasada",
            xaxis_title="Tipo de Combustible",
            yaxis_title="Precio (€)",
            legend_title="Día",
            barmode='group',
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}comparativaPrecioSemanaPasada.html", include_plotlyjs=False, full_html=False)

        fig = go.Figure(data=[
            go.Bar(
                name = f"Mes Pasado {datosMesPasado.head(1)['Fecha'].values[0]}",
                x = datosMesPasado.head(1).columns[1:].values,
                y = datosMesPasado.head(1).iloc[:, 1:].values[0],
                text = datosMesPasado.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                hovertemplate="<br>".join([
                    "Combustible: %{x}",
                    "Precio (€): %{y}",
                ])
            ),
            go.Bar(
                name = f"Hoy {datosHoy.head(1)['Fecha'].values[0]}",
                x = datosHoy.head(1).columns[1:].values,
                y = datosHoy.head(1).iloc[:, 1:].values[0],
                text = datosHoy.head(1).iloc[:, 1:].values[0],
                textposition = 'auto',
                hovertemplate="<br>".join([
                    "Combustible: %{x}",
                    "Precio (€): %{y}",
                ])
            )
        ])
        fig.update_layout(
            title="Comparativa precios combustible entre el día actual y el mes pasado",
            xaxis_title="Tipo de Combustible",
            yaxis_title="Precio (€)",
            legend_title="Día",
            barmode='group',
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_GENERAL']}comparativaPrecioMesPasado.html", include_plotlyjs=False, full_html=False)
        
    def __generarGraficosCCAA(self):
        for combustible in self.__dfCCAA.columns[2:-2]:
            fig = px.line(self.__dfCCAA, x='Fecha', y=combustible, color='CCAA', markers=True, title=f"Evolución del precio del {combustible.replace('Precio ', '')} por Comunidad Autónoma")
            
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            fig.update_layout(
                xaxis = dict(
                    tickmode = "array",
                    tickvals = self.__fechas,
                    ticktext = self.__fechas
                )
            )

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
                        mode = "lines+markers",
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
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            xaxis = dict(
                tickmode = "array",
                tickvals = self.__fechas,
                ticktext = self.__fechas
            )
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_CCAA']}comparativaPrecios.html", include_plotlyjs=False, full_html=False)
    
    def __generarGraficosProvincias(self):
        for combustible in self.__dfProvincia.columns[2:-2]:
            fig = px.line(self.__dfProvincia, x='Fecha', y=combustible, color='Provincia', markers=True, title=f"Evolución del precio del {combustible.replace('Precio ', '')} por Provincias")
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            fig.update_layout(
                xaxis = dict(
                    tickmode = "array",
                    tickvals = self.__fechas,
                    ticktext = self.__fechas
                )
            )
        
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
                        mode = "lines+markers",
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
            # Modificamos las etiquetas del eje X para que únicamente aparezca la primera y la última fecha de la que se disponen datos y así evitar que se superpongan
            xaxis = dict(
                tickmode = "array",
                tickvals = self.__fechas,
                ticktext = self.__fechas
            )
        )
        plo.io.write_html(fig, f"{self.__config['VISUALIZACION']['RUTA_GUARDAR_PROVINCIA']}comparativaPrecios.html", include_plotlyjs=False, full_html=False)