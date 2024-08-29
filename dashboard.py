# IMPORTS
import streamlit as st
import altair as alt 
import pandas as pd
import numpy as np
import panel as pn
import datetime as dt
pn.extension('vega')


###################################
# Gráfico 1: Generación eléctrica por tecnologías en España
###################################

# Preprocesamiento de datos

def prep_g1(df_G):
    
    # Convertir la columna datetime a tipo datetime
    df_G['datetime'] = pd.to_datetime(df_G['datetime'], utc = True)
    df_G['date'] = df_G['datetime'].dt.date

    # Convertir la columna value a tipo float
    df_G['value'] = df_G['value'].astype(float)

    # Convertir la columna name a tipo categoría
    df_G['name'] = df_G['name'].astype('category')

    # Elimino las columnas vacías
    df_G = df_G.drop(['geoid', 'geoname'], axis=1)

    # Elimino la categoria total (no es relevante en este caso) y adapto nombres
    df_G = df_G.drop(df_G[df_G['id']== 10195].index)
    df_G['name'] = df_G['name'].str.slice(18)
    
    return df_G
    

# Filtrar los datos en función de la fecha seleccionada
def get_plot_generacion_dia(date, df):

    date = date.date()
    
    # Crear una máscara de filtro para la fecha seleccionada
    mask = (df['date'] == date)
    df_filtered = df.loc[mask]
    
    # Mostrar los datos filtrados para depuración
    st.write("Datos filtrados:", date)

    # Crear el gráfico Altair
    selection = alt.selection_point(fields=['name'], bind='legend')

    chart = alt.Chart(df_filtered).mark_area(interpolate='step').encode(
        x=alt.X('datetime:T', title='Hora del día'),  # Eje X: Hora del día
        y=alt.Y('sum(value):Q', title='Potencia eléctrica (MW)', scale=alt.Scale(domain=[0, 42000])),  # Suma de potencia
        color=alt.Color('name:N', title='Tecnología'),  # Diferenciar por tecnología
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).properties(
        title='Generación eléctrica por tecnología',
        width=700,
        height=400
    ).add_params(selection)

    return chart

###################################
# Gráfico 2: Generación eléctrica por tecnologías en España (media diaria)
###################################

# Filtrar los datos en función de la fecha seleccionada
def get_plot_generacion_dia_media(date, df):

    date = date.date()
    
    # Crear una máscara de filtro para la fecha seleccionada
    mask = (df['date'] == date)
    df_filtered = df.loc[mask]
    
    df_filtered = df_filtered.groupby('name')['value'].sum().sort_values(ascending=False).reset_index()
    
    # Calcular la suma total de la columna 'value'
    total_sum = df_filtered['value'].sum()

    # Normalizar la columna 'value' a un 100%
    df_filtered['value_normalized'] = (df_filtered['value'] / total_sum)
    
    # Mostrar los datos filtrados para depuración
    st.write("Día seleccionado:", date)

    # Crear el gráfico Altair
    selection = alt.selection_point(fields=['name'], bind='legend', empty='none')

    chart = alt.Chart(df_filtered).mark_arc().encode(
    theta="value_normalized",
    color=alt.Color('name:N', title='Tecnología'),  # Diferenciar por tecnología
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).properties(
        title='Proporción de generación eléctrica media diaria por tecnología',
        width=800,
        height=500
    ).add_params(selection)
    
    
    # Añadir un texto para mostrar el porcentaje del segmento seleccionado
    text = alt.Chart(df_filtered).mark_text(
        radiusOffset=200,  # Ajusta la distancia del texto desde el centro
        size=30,          # Tamaño del texto
        fontWeight='bold' # Hacer el texto en negrita para destacarlo
    ).encode(
        theta=alt.Theta("value_normalized:Q", stack=True),
        text=alt.Text('value_normalized:Q', format=".0%"),
        color=alt.condition(selection, alt.value('black'), alt.value('transparent')),
        # Asegurarse de que solo el texto del segmento seleccionado se muestre
        opacity=alt.condition(selection, alt.value(1), alt.value(0))
    ).transform_filter(
        selection
    )

    return chart + text



###################################
# Gráfico 3: Generación eléctrica por tecnologías en España (anual)
###################################

# Preprocesamiento de datos

def prep_g3(df):

    # Elimino la categoria total (no es relevante en este caso) y adapto nombres
    df = df.drop(df[df['id']== 10195].index)
    df['name'] = df['name'].str.slice(18)
    
    df = df.groupby('name')['value'].sum().sort_values(ascending=False).reset_index()

    # Calcular la suma total de la columna 'value'
    total_sum = df['value'].sum()

    # Normalizar la columna 'value' a un 100%
    df['value_normalized'] = (df['value'] / total_sum)
    
    return df

# Filtrar los datos en función de la fecha seleccionada
def get_plot_generacion_anual(df):
    selection = alt.selection_point(fields=['name'], bind='legend')

    # Base del gráfico
    base = alt.Chart(df).transform_window(
        rank='rank(value)',
        sort=[alt.SortField('value', order='descending')]
    ).encode(
        alt.Theta("value:Q", sort=df['name'].to_list()).stack(True),
        alt.Radius("value").scale(type="sqrt", zero=True),
        color=alt.Color("name:N", title='Tecnología'),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_params(selection).properties(
        title='Generación eléctrica anual por tecnología',
        width=680,
        height=500
    )

    # Gráfico de arco
    c1 = base.mark_arc(innerRadius=12, stroke="#fff")

    # Gráfico de texto con formato
    c2 = base.mark_text(radiusOffset=10, size=20).encode(
        text=alt.Text("value_normalized:Q", format=".0%")
        ).transform_filter(
        alt.datum.rank <= 6
    )
        
    return c1 + c2



###################################
# Gráfico 4: Generación eléctrica por tecnologías en España (mensual)
###################################

# Preprocesamiento de datos

def prep_g4(df):

    # Elimino la categoria total (no es relevante en este caso) y adapto nombres
    df = df.drop(df[df['id']== 10195].index)
    df['name'] = df['name'].str.slice(18)
    
    # Creo una columna llamada Month
    df['datetime'] = pd.to_datetime(df['datetime'], utc = True)
    df['month'] = df['datetime'].dt.month
    df = df.groupby(['month', 'name']).agg({'value': 'sum'}).reset_index()

    return df

# Filtrar los datos en función de la fecha seleccionada
def get_plot_generacion_mensual(df):
    selection = alt.selection_point(fields=['name'], bind='legend')
    
    chart = alt.Chart(df).mark_bar(size=20).encode(
        x = alt.X('month', title='Mes de 2023', scale=alt.Scale(domain=[1, 12])),
        y=alt.Y('sum(value):Q', title='Energía producida (MWh)', scale=alt.Scale(domain=[0, 24000000])),
        color=alt.Color("name:N", title='Tecnología'),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_params(selection).properties(
        title='Generación eléctrica mensual por tecnología',
        width=680,
        height=500
    )

    return chart





#####################################################
## Carga de datos
#####################################################

# Gráfico 1: Generación por tecnologías
graf1_path = 'Datos/Generacion/GeneracionTotal_2023_h.csv'
df_gen = pd.read_csv(graf1_path, delimiter=';')

# Preprocesamiento
df_G1 = df_gen.copy()
df_G1 = prep_g1(df_G1)



# Gráfico 3: Generación por tecnologias anual
df_G3 = df_gen.copy()
df_G3 = prep_g3(df_G3)


# Gráfico 4: Generación por tecnologias mensual
df_G4 = df_gen.copy()
df_G4 = prep_g4(df_G4)

#####################################################
# Configuración de la web
#####################################################

# Configuracion de páginas

st.set_page_config(
    page_title="Generación eléctrica española 2023",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# Estructura de la web

tab1, tab2, tab3, tab4 = st.tabs(["Generación por tecnologías", "Precio de la electricidad", "Impacto medioambiental", "Resumen"])

with tab1:
    
    # Título
    st.header("Generación eléctrica por tecnologías en España")
    
    
    # Crear el slider de fecha en Streamlit
    # Configuración inicial del slider de fecha
    start_date = dt.datetime(2023, 1, 1)
    end_date = dt.datetime(2023, 12, 31)
    selected_date = st.slider(
        'Seleccione una fecha',
        min_value=start_date,
        max_value=end_date,
        value=start_date,
        format="YYYY-MM-DD"
    )
   
    st.altair_chart(get_plot_generacion_dia(selected_date, df_G1), use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
         st.altair_chart(get_plot_generacion_dia_media(selected_date, df_G1))
    with col2:
        None
        
    col3, col4 = st.columns(2)
    
    with col3:
        st.altair_chart(get_plot_generacion_anual(df_G3))
    with col4:
        st.altair_chart(get_plot_generacion_mensual(df_G4))
