[![Workflow Obtener precio de los combustibles](https://github.com/jmsimonramos/precio-combustible-ESP/actions/workflows/obtenerPrecioCombustible.yml/badge.svg?branch=main)](https://github.com/jmsimonramos/precio-combustible-ESP/actions/workflows/obtenerPrecioCombustible.yml)

[![pages-build-deployment](https://github.com/jmsimonramos/precio-combustible-ESP/actions/workflows/pages/pages-build-deployment/badge.svg?branch=main)](https://github.com/jmsimonramos/precio-combustible-ESP/actions/workflows/pages/pages-build-deployment)

## 脥ndice
1. [馃搳 Dashboard Interactivo](#Dashboard)
2. [馃摑 Introducci贸n](#Introducci贸n)
3. [馃捒 Obtenci贸n de los Datos](#Obtenci贸n_De_Los_Datos)
4. [馃摎 Conjuntos de Datos](#Conjuntos_De_Datos)
5. [鉀斤笍 Dataset Estaciones de Servicio](#Dataset_Estaciones_De_Servicio)
6. [馃挾 Dataset Precio Combustible Mensual](#Dataset_Precio_Combustible_Mensual)
7. [馃椇 Dataset precio combustible mensual (por Comunidades Aut贸nomas)](#Dataset_Precio_Combustible_MensualCCAA)
8. [馃搷 Dataset precio combustible mensual (por Provincias)](#Dataset_Precio_Combustible_MensualProvincia)
9. [馃洜 Pruebas de Ejecuci贸n](#Pruebas_De_Ejecuci贸n)
10. [鈿欙笍 Estructura del Repositorio](#Estructura)

# 馃搳 Dashboard Interactivo <a name="Dashboard"></a>
<a href="https://jmsimonramos.github.io/precio-combustible-ESP/" target="_blank">Visualizaci贸n de los datos de forma interactiva</a>

# 馃摑 Introducci贸n <a name="Introducci贸n"></a>

El objetivo del repositorio consiste en disponer de una forma abierta y f谩cilmente accesible el hist贸rico de los precios de los combustibles en las distintas estaciones de servicio de Espa帽a. Esto se debe a que la fuente oficial de la que se ha extra铆do esta informaci贸n ([Datos Abiertos del Gobierno de Espa帽a](https://datos.gob.es/es/catalogo/e05068001-precio-de-carburantes-en-las-gasolineras-espanolas)) proporciona estos datos de forma diaria, pero el acceso al hist贸rico de precios es m谩s tedioso y es necesario establecer un gran n煤mero de filtros para obtener esta informaci贸n. Debido a ello, esta propuesta busca proporcionar un conjunto de datos en el que se muestren los precios diarios de los combustibles en todas las estaciones de servicio espa帽olas de una forma m谩s r谩pida y eficiente.

# 馃捒 Obtenci贸n de los datos <a name="Obtenci贸n_De_Los_Datos"></a>

La obtenci贸n de los datos se realiza de forma autom谩tica a partir del un servicio REST oficial de [Datos Abiertos del Gobierno de Espa帽a](https://datos.gob.es/es/catalogo/e05068001-precio-de-carburantes-en-las-gasolineras-espanolas) (Ver Figura 1 y 2). Todos los d铆as se ejecuta el script *obtenerPrecioCombustible.py* el cu谩l procesa la informaci贸n de los precios, elimina las columnas innecesarias y le a帽ade la fecha del d铆a actual para as铆 poder filtrar por ella posteriormente.

![Pagina Datos Abiertos Gob](assets/paginaGob.png)
**Figura 1: P谩gina oficial de los Datos Abiertos del Gobierno de Espa帽a.**

![Datos en crudo](assets/datosRaw.png)
**Figura 2: Datos en crudo de las Estaciones de Servicio y los precios del combustible.**

El motivo de eliminar columnas se debe a que cada uno de los registros que devuelve la respuesta cuenta con toda la informaci贸n de la estaci贸n de servicio: precios del combustible, datos postales, coordenadas, marca, etc. Dado que esta informaci贸n no var铆a, se ha extra铆do a un fichero fijo aparte *EESSS.csv*. De esta forma se dispone de un fichero est谩tico con los datos concretos de las estaciones de servicio (Ver Figura 3), y un fichero din谩mico que se va actualizando con los datos de la fecha de consulta, el identificador de la estaci贸n de servicio, y los precios del combustible en dicha estaci贸n (Ver Figura 4). Gracias a esto se consigue reducir el tama帽o de los conjuntos de datos, evitando almacenar de forma reiterada informaci贸n redundante.

![Datos Estaciones de Servicio Procesadas](assets/datosEESSProcesados.png)
**Figura 3: Datos procesados de las Estaciones de Servicio.**

![Datos Precio Combustible Procesado](assets/datosPrecioCombustibleProcesados.png)
**Figura 4: Datos procesados de los precios del combustible en las distintas Estaciones de Servicio.**
# 馃摎 Conjuntos de datos <a name="Conjuntos_De_Datos"></a>

Como se ha mencionado anteriormente, se ha dividido la informaci贸n en dos conjuntos de datos distintos: *data/EESS.csv*, con la informaci贸n de la Estaci贸n de Servicio; y *data/historico/precioEESS-{mes}-{a帽o}.csv*, con los precios del combustible en cada Estaci贸n de Servicio para cada uno de los d铆as de un determinado mes.

La forma de combinar los datos de ambos conjuntos es mediante el atributo **IDEESS**.

## 鉀斤笍 Dataset Estaciones de Servicio <a name="Dataset_Estaciones_De_Servicio"></a>

El conjunto de datos *EESS.csv* se encuentra formado por los siguientes atributos:

| **Atributo**     | **Descripcion**                                                                                   | **Tipo** |
|------------------|---------------------------------------------------------------------------------------------------|----------|
| IDEESS           | Identificador 煤nico de la Estaci贸n de Servicio                                                    | Str      |
| Direccion        | Direcci贸n de la Estaci贸n de Servicio                                                              | Str      |
| Horario          | Horario de la Estaci贸n de Servicio                                                               | Str      |
| Rotulo           | Rotulo o Marca de la Estaci贸n de Servicio                                                         | Str      |
| Margen           | Margen de la carretera en el que se encuentra: I = Izquierdo; D = Derecho; N = No aplica          | Str      |
| Tipo Venta       | Indica el tipo de venta de la Estaci贸n de Servicio: P = Publico General; R = Restringida a socios | Str      |
| Remision         | Procedencia del combustible: OM = Operador Mayorista; dm = Distribuidor minorista                 | Str      |
| Latitud          | Latitud de las coordenadas en la que se encuentra la Estaci贸n de Servicio                         | Float    |
| Longitud (WGS84) | Longitud de las coordenadas en la que se encuentra la Estaci贸n de Servicio                        | Float    |
| Municipio        | Municipio al que pertenece la Estaci贸n de Servicio                                                | Str      |
| C.P.             | C贸digo Postal del municipio al que pertenece la Estaci贸n de Servicio                              | Str      |
| Provincia        | Provincia a la que pertenece la Estaci贸n de Servicio                                              | Str      |
| CCAA           | Nombre de la Comunidad Aut贸noma a la que pertenece la Estaci贸n de Servicio                 | Str      |

## 馃挾 Dataset precio combustible mensual <a name="Dataset_Precio_Combustible_Mensual"></a>

El conjunto de datos *precioEESS-{mes}-{a帽o}.csv* se encuentra formado por los siguientes atributos:

| **Atributo**                       | **Descripcion**                                                      | **Tipo** |
|------------------------------------|----------------------------------------------------------------------|----------|
| Fecha                              | Fecha a la que pertenecen los precios                                | Str      |
| IDEESS                             | Identificador de la Estaci贸n de Servicio                             | Str      |
| Precio Biodiesel                   | Precio del Biodiesel en la Estaci贸n de Servicio                      | Float    |
| Precio Bioetanol                   | Precio del Bioetanol en la Estaci贸n de Servicio                      | Float    |
| Precio Gas Natural Comprimido      | Precio del Gas Natural Comprimido en la Estaci贸n de Servicio         | Float    |
| Precio Gas Natural Licuado         | Precio del Gas Natural Licuado en la Estaci贸n de Servicio            | Float    |
| Precio gases licuados del petroleo | Precio de los gases licuados del petroleo en la Estaci贸n de Servicio | Float    |
| Precio Gasoleo A                   | Precio del Gas贸leo A en la Estaci贸n de Servicio                      | Float    |
| Precio Gasoleo B                   | Precio del Gas贸leo B en la Estaci贸n de Servicio                      | Float    |
| Precio Gasoleo Premium             | Precio del Gas贸leo Premium en la Estaci贸n de Servicio                | Float    |
| Precio Gasolina 95 E10             | Precio de la Gasolina 95 E10 en la Estaci贸n de Servicio              | Float    |
| Precio Gasolina 95 E5              | Precio de la Gasolina 95 E5 en la Estaci贸n de Servicio               | Float    |
| Precio Gasolina 95 E5 Premium      | Precio de la Gasolina 95 E5 Premium en la Estaci贸n de Servicio       | Float    |
| Precio Gasolina 98 E10             | Precio de la Gasolina 98 E10 en la Estaci贸n de Servicio              | Float    |
| Precio Gasolina 98 E5              | Precio de la Gasolina 98 E5 en la Estaci贸n de Servicio               | Float    |
| % BioEtanol                        | Porcentaje de BioEtanol                                              | Float    |
| % 脡ster met铆lico                   | Porcentaje de 茅ster met铆lico                                         | Float    |


## 馃椇 Dataset precio combustible mensual (por Comunidades Aut贸nomas) <a name="Dataset_Precio_Combustible_MensualCCAA"></a>

El conjunto de datos *precioCCAA-{mes}-{a帽o}.csv* se encuentra formado por los siguientes atributos:

| **Atributo**                       | **Descripcion**                                                      | **Tipo** |
|------------------------------------|----------------------------------------------------------------------|----------|
| Fecha                              | Fecha a la que pertenecen los precios                                | Str      |
| CCAA                             | Nombre de la Comunidad Aut贸noma                             | Str      |
| Precio Biodiesel                   | Precio del Biodiesel en la Estaci贸n de Servicio                      | Float    |
| Precio Bioetanol                   | Precio del Bioetanol en la Estaci贸n de Servicio                      | Float    |
| Precio Gas Natural Comprimido      | Precio del Gas Natural Comprimido en la Estaci贸n de Servicio         | Float    |
| Precio Gas Natural Licuado         | Precio del Gas Natural Licuado en la Estaci贸n de Servicio            | Float    |
| Precio gases licuados del petroleo | Precio de los gases licuados del petroleo en la Estaci贸n de Servicio | Float    |
| Precio Gasoleo A                   | Precio del Gas贸leo A en la Estaci贸n de Servicio                      | Float    |
| Precio Gasoleo B                   | Precio del Gas贸leo B en la Estaci贸n de Servicio                      | Float    |
| Precio Gasoleo Premium             | Precio del Gas贸leo Premium en la Estaci贸n de Servicio                | Float    |
| Precio Gasolina 95 E10             | Precio de la Gasolina 95 E10 en la Estaci贸n de Servicio              | Float    |
| Precio Gasolina 95 E5              | Precio de la Gasolina 95 E5 en la Estaci贸n de Servicio               | Float    |
| Precio Gasolina 95 E5 Premium      | Precio de la Gasolina 95 E5 Premium en la Estaci贸n de Servicio       | Float    |
| Precio Gasolina 98 E10             | Precio de la Gasolina 98 E10 en la Estaci贸n de Servicio              | Float    |
| Precio Gasolina 98 E5              | Precio de la Gasolina 98 E5 en la Estaci贸n de Servicio               | Float    |
| % BioEtanol                        | Porcentaje de BioEtanol                                              | Float    |
| % 脡ster met铆lico                   | Porcentaje de 茅ster met铆lico                                         | Float    |

## 馃搷 Dataset precio combustible mensual (por Provincias) <a name="Dataset_Precio_Combustible_MensualProvincia"></a>

El conjunto de datos *precioPROVINCIA-{mes}-{a帽o}.csv* se encuentra formado por los siguientes atributos:

| **Atributo**                       | **Descripcion**                                                      | **Tipo** |
|------------------------------------|----------------------------------------------------------------------|----------|
| Fecha                              | Fecha a la que pertenecen los precios                                | Str      |
| Provincia                             | Nombre de la Comunidad Provincia                             | Str      |
| Precio Biodiesel                   | Precio del Biodiesel en la Estaci贸n de Servicio                      | Float    |
| Precio Bioetanol                   | Precio del Bioetanol en la Estaci贸n de Servicio                      | Float    |
| Precio Gas Natural Comprimido      | Precio del Gas Natural Comprimido en la Estaci贸n de Servicio         | Float    |
| Precio Gas Natural Licuado         | Precio del Gas Natural Licuado en la Estaci贸n de Servicio            | Float    |
| Precio gases licuados del petroleo | Precio de los gases licuados del petroleo en la Estaci贸n de Servicio | Float    |
| Precio Gasoleo A                   | Precio del Gas贸leo A en la Estaci贸n de Servicio                      | Float    |
| Precio Gasoleo B                   | Precio del Gas贸leo B en la Estaci贸n de Servicio                      | Float    |
| Precio Gasoleo Premium             | Precio del Gas贸leo Premium en la Estaci贸n de Servicio                | Float    |
| Precio Gasolina 95 E10             | Precio de la Gasolina 95 E10 en la Estaci贸n de Servicio              | Float    |
| Precio Gasolina 95 E5              | Precio de la Gasolina 95 E5 en la Estaci贸n de Servicio               | Float    |
| Precio Gasolina 95 E5 Premium      | Precio de la Gasolina 95 E5 Premium en la Estaci贸n de Servicio       | Float    |
| Precio Gasolina 98 E10             | Precio de la Gasolina 98 E10 en la Estaci贸n de Servicio              | Float    |
| Precio Gasolina 98 E5              | Precio de la Gasolina 98 E5 en la Estaci贸n de Servicio               | Float    |
| % BioEtanol                        | Porcentaje de BioEtanol                                              | Float    |
| % 脡ster met铆lico                   | Porcentaje de 茅ster met铆lico                                         | Float    |

# 馃洜 Pruebas de Ejecuci贸n <a name="Pruebas_De_Ejecuci贸n"></a>

Para ejecutar el script hay que ejecutar el comando `python obtenerPrecioCombustible.py` desde la ra铆z del proyecto.

![Prueba de Ejecuci贸n Correcta](assets/demoPrincipal.gif)
**Video 1: Ejecuci贸n correcta del script.**

![Prueba de Ejecuci贸n cuando ya existen datos](assets/demoExistenDatos.gif)
**Video 2: Ejecuci贸n del script cuando ya se disponen de los datos del d铆a.**

# 鈿欙笍 Estructura del Repositorio <a name="Estructura"></a>

El repositorio se encuentra estructurado de la siguiente forma:

````
.
鈹溾攢鈹? .github/ # Workflow para obtener los datos y generar el dashboard autom谩ticamente
鈹溾攢鈹? assets/ # Im谩genes del README
鈹溾攢鈹? data/ # Datos para generar las visualizaciones
鈹溾攢鈹? docs/ # Dashboard con la visualizaci贸n de los precios
鈹溾攢鈹? notebooks/ # Ficheros .ipynb adicionales
鈹溾攢鈹? src/ # Ficheros .py con el c贸digo para obtener los datos, procesarlos y generar las visualizaciones
鈹溾攢鈹? config.json # Fichero con la configuraci贸n de los par谩metros del script de obtenci贸n de los precios y la visualizaci贸n
鈹溾攢鈹? obtenerPrecioCombustible.py # Script de obtenci贸n de precios y generaci贸n de gr谩ficas
鈹溾攢鈹? README.md
鈹斺攢鈹? requirements.txt # Dependencias python para ejecutar la herramienta
````