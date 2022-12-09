# Trabajo Final curso Programación SIG
# Autor: Oscar Leandro Rodríguez Bolaños
# Carné: B86648

import streamlit as st

import pandas as pd
import geopandas as gpd

import plotly.express as px

import folium
from folium import Marker
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from streamlit_folium import folium_static
from streamlit_folium import st_folium


import math


#
# Configuración de la página
#
st.set_page_config(layout='wide')



#
# TÍTULO Y DESCRIPCIÓN DE LA APLICACIÓN
#

st.title('Analisis de especies')
st.markdown('Alumno: Oscar Leandro Rodríguez Bolaños')

# Carga de datos
archivo_registros_presencia = st.sidebar.file_uploader('Seleccione un archivo CSV que siga el estándar DwC')

# Se continúa con el procesamiento solo si hay un archivo de datos cargado
if archivo_registros_presencia is not None:
    # Carga de registros de presencia en un dataframe
    registros_presencia = pd.read_csv(archivo_registros_presencia, delimiter='\t')
    # Conversión del dataframe de registros de presencia a geodataframe
    registros_presencia = gpd.GeoDataFrame(registros_presencia, 
                                           geometry=gpd.points_from_xy(registros_presencia.decimalLongitude, 
                                                                       registros_presencia.decimalLatitude),
                                           crs='EPSG:4326')

    # Carga de polígonos de ASP
    asp = gpd.read_file("datos/cantones.geojson")

    # Limpieza de datos
    # Eliminación de registros con valores nulos en la columna 'species'
    registros_presencia = registros_presencia[registros_presencia['species'].notna()]
    # Cambio del tipo de datos del campo de fecha
    registros_presencia["eventDate"] = pd.to_datetime(registros_presencia["eventDate"])

    # Especificación de filtros
    # Especie
    lista_especies = registros_presencia.species.unique().tolist()
    lista_especies.sort()
    filtro_especie = st.sidebar.selectbox('Seleccione la especie', lista_especies)


    #
    # PROCESAMIENTO
    #

    # Filtrado
    registros_presencia = registros_presencia[registros_presencia['species'] == filtro_especie]

    # Cálculo de la cantidad de registros en ASP
    # "Join" espacial de las capas de ASP y registros de presencia
    asp_contienen_registros = asp.sjoin(registros_presencia, how="left", predicate="contains")
    asp_contienen_registros2 = asp.sjoin(registros_presencia, how="left", predicate="contains")
    # Conteo de registros de presencia en cada ASP
    asp_registros = asp_contienen_registros.groupby("CANTO").agg(cantidad_registros_presencia = ("gbifID","count"))
    asp_registros = asp_registros.reset_index() # para convertir la serie a dataframe

    asp_registros2 = asp_contienen_registros2.groupby("PROV").agg(cantidad_registros_presencia2 = ("gbifID","count"))
    asp_registros2 = asp_registros2.reset_index() # para convertir la serie a dataframe

    #
    # SALIDAS
    #

    # Tabla de registros de presencia
    st.header('Registros de presencia')
    st.dataframe(registros_presencia[['species', 'stateProvince', 'locality','eventDate']].rename(columns = {'species':'Especie', 'stateProvince':'Provincia', 'locality':'Localidad', 'eventDate':'Fecha'}))


    # Definición de columnas
    col1, col2 = st.columns(2)

    # Gráficos de cantidad de registros de presencia por ASP
    # "Join" para agregar la columna con el conteo a la capa de ASP
    asp_registros2 = asp_registros2.join(asp.set_index('PROV'))
    # Dataframe filtrado para usar en graficación
    asp_registros_grafico = asp_registros2.loc[asp_registros2['cantidad_registros_presencia2'] > 0, 
                                                            ["NPROVINCIA", "cantidad_registros_presencia2"]].sort_values("cantidad_registros_presencia2")
    asp_registros_grafico = asp_registros_grafico.set_index('NPROVINCIA')  

    with col1:
        st.header('Cantidad de registros por ASP')

        fig = px.bar(asp_registros_grafico, 
                    labels={'NPROVINCIA':'Provincia', 'cantidad_registros_presencia2':'Registros de presencia'})
        st.plotly_chart(fig) 


    # Gráficos de cantidad de registros de
    # "Join" para agregar la columna con el conteo a la capa de ASP
    asp_registros = asp_registros.join(asp.set_index('CANTO'))
    # Dataframe filtrado para usar en graficación
    asp_registros_grafico = asp_registros.loc[asp_registros['cantidad_registros_presencia'] > 0, 
                                                            ["NCANTON", "cantidad_registros_presencia"]].sort_values("cantidad_registros_presencia")
    asp_registros_grafico = asp_registros_grafico.set_index('NCANTON')  

    with col1:
        st.header('Cantidad de registros po')

        fig = px.bar(asp_registros_grafico, 
                    labels={'nombre_asp':'ASP', 'cantidad_registros_presencia':'Registros de presencia'})
        st.plotly_chart(fig) 






        # Mapa de calor y de registros agrupados
        st.header('Mapa de calor y de registros agrupados')
        # Capa base
        m = folium.Map(location=[9.6, -84.2], tiles='CartoDB dark_matter', zoom_start=8)
        folium.TileLayer(tiles='CartoDB positron', zoom_start=8).add_to(m)

        folium.Map(location=[9.6, -84.2], tiles='Stamen Terrain', zoom_start=8).add_to(m)


        HeatMap(data=registros_presencia[['decimalLatitude', 'decimalLongitude']],
                name='Mapa de calor').add_to(m)
        # Capa de ASP
        folium.GeoJson(data=asp, name='asp').add_to(m)
        # Capa de registros de presencia agrupados
        mc = MarkerCluster(name='Registros agrupados')
        for idx, row in registros_presencia.iterrows():
            if not math.isnan(row['decimalLongitude']) and not math.isnan(row['decimalLatitude']):
                        mc.add_child(Marker([row['decimalLatitude'], row['decimalLongitude']], 
                            popup=[row['species'], 
                            row['stateProvince'], 
                            row['locality'], 
                            row['eventDate']])).add_to(m)
        m.add_child(mc)



        # Mapa de coropletas
        folium.Choropleth(
            name="Cantidad de registros en provincias",
            geo_data=asp,
            data=asp_registros2,
            columns=["PROV", 'cantidad_registros_presencia2'],
            bins=8,
            key_on='feature.properties.PROV',
            fill_color='Reds', 
            fill_opacity=0.5, 
            line_opacity=1,
            legend_name='Cantidad de registros de presencia').add_to(m)
        # Mapa de coropletas numero 2
        folium.Choropleth(
            name="Cantidad de registro",
            geo_data=asp,
            data=asp_registros,
            columns=['CANTO', 'cantidad_registros_presencia'],
            bins=8,
            key_on='feature.properties.CANTO',
            fill_color='Reds', 
            fill_opacity=0.5, 
            line_opacity=1,
            legend_name='Cantidad de registros en cantones').add_to(m)
        # Control de capas
        folium.LayerControl().add_to(m)    
        # Despliegue del mapa
        folium_static(m)