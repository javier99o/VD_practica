# IMPORTS
import streamlit as st
import altair as alt 
import pandas as pd
import numpy as np
#import panel as pn
#pn.extension('vega')
import datetime as dt



###################################
# Gráfico A.1: Generación eléctrica por tecnologías en España
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
        title='Generación eléctrica por tecnología (diario)',
        width=700,
        height=400
    ).add_params(selection)

    return chart

###################################
# Gráfico A.2: Generación eléctrica por tecnologías en España (media diaria)
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
        radiusOffset=20,  # Ajusta la distancia del texto desde el centro
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
# Gráfico A.3: Generación eléctrica por tecnologías en España (anual)
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

    # Grafico de arco
    c1 = base.mark_arc(innerRadius=12, stroke="#fff")

    # Grafico de texto con formato
    c2 = base.mark_text(radiusOffset=20, size=20).encode(
        text=alt.Text("value_normalized:Q", format=".0%")
        ).transform_filter(
        alt.datum.rank <= 6
    )
        
    return c1 + c2


###################################
# Gráfico A.4: Generación eléctrica por tecnologías en España (mensual)
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


###################################
# Gráfico B.1: Desglose horario de precio España
###################################

# Preprocesamiento de datos

def prep_b1(df):
    # Seleccionar solo las columnas de interés
    df = df[['id', 'name', 'value', 'datetime']]

    # Convertir la columna datetime a tipo datetime
    df['datetime'] = pd.to_datetime(df['datetime'], utc = True) #, utc = True

    # Convertir la columna name a tipo categoría
    df['name'] = df['name'].astype('category')

    # Limpieza de datos
    df = df.drop(df[df['id']== 10211].index)
    df['name'] = df['name'].str.slice(32).str.capitalize()
    df['date'] = df['datetime'].dt.date

    return df


# Filtrar los datos en función de la fecha seleccionada
def get_plot_precio_hora(date, df):

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
        y=alt.Y('value:Q', title='Precio por MWh (€/MWh)', scale=alt.Scale(domain=[-10, 250])),
        color=alt.Color('name:N', title='Concepto'),  # Diferenciar por tecnología
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
        order=alt.Order('sum(value):Q', sort='descending')
    ).properties(
        title='Precio electricidad',
        width=400,
        height=400
    ).add_params(selection)

    return chart

def prices(date, df):
    date = date.date()
    
    # Crear una máscara de filtro para la fecha seleccionada
    mask = (df['date'] == date)
    df_filtered = df.loc[mask]

    df_filtered = df_filtered.groupby('datetime')['value'].sum().reset_index()

    avg = df_filtered['value'].mean()
    min = df_filtered['value'].min()
    max = df_filtered['value'].max()

    return avg, min, max

###################################
# Gráfico B.2: Desglose horario de precio EU
###################################

# Preprocesamiento de datos

def prep_b2(df):
    # Seleccionar solo las columnas de interés
    df = df[['id', 'name', 'value', 'datetime']]

    # Convertir la columna datetime a tipo datetime
    df['datetime'] = pd.to_datetime(df['datetime'], utc = True) #, utc = True

    # Convertir la columna name a tipo categoría
    df['name'] = df['name'].astype('category')

    # Limpieza de datos
    df = df.drop(df[df['id']== 1001].index)
    df['name'] = df['name'].str.slice(27).str.capitalize()
    df['date'] = df['datetime'].dt.date

    return df


def get_plot_precio_hora_eu(date, df):
    date = date.date()
    
    # Crear una máscara de filtro para la fecha seleccionada
    mask = (df['date'] == date)
    df_filtered = df.loc[mask]
    
    # Mostrar los datos filtrados para depuración
    st.write("Datos filtrados:", date)

    order = ['Alemania','Bélgica','España','Francia','Italia','Países bajos','Portugal','Reino unido']
    # Convertir la columna 'category' a un tipo categórico con el orden definido
    df['name'] = pd.Categorical(df['name'], categories=order, ordered=True)
    
    # Ordenar el DataFrame según la columna 'category'
    df = df.sort_values('name')

    selection = alt.selection_point(fields=['name'], bind='legend')

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection_point(nearest=True, on="mouseover",
                             fields=["datetime"], empty=False)
    
    # The basic line
    line = alt.Chart(df_filtered).mark_line(interpolate='step').encode(
              x=alt.X('datetime:T', title='Hora del día'),  # Eje X: Hora del día
              y=alt.Y('value:Q', title='Precio por MWh (€/MWh)', scale=alt.Scale(domain=[-10, 300])),
              color=alt.Color('name:N', title='País'), 
              opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
              ).properties(
              title='Precio electricidad por paises',
              width=700,
              height=400
              ).add_params(selection)
    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
         opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
    
    # Draw a rule at the location of the selection
    rules = alt.Chart(df_filtered).transform_pivot(
       "name",
       value="value",
       groupby=["datetime"]).mark_rule(color="gray").encode(
        x="datetime",
        opacity=alt.condition(nearest, alt.value(0.3), alt.value(0)),
        tooltip=[alt.Tooltip(c, type="quantitative") for c in order],
    ).add_params(nearest)
    # Put the five layers into a chart and bind the data
    chart = alt.layer(
        line, points, rules
    ).properties(
        width=600, height=300
    )
    return chart


###################################
# Gráfico C.1: Emisiones medias diarias
###################################

# Preprocesamiento de datos

def prep_c1(df):
    # Convertir la columna datetime a tipo datetime
    df['datetime'] = pd.to_datetime(df['datetime'], utc = True) 
    df['date'] = df['datetime'].dt.date
    
    df = pd.melt(df, id_vars=['datetime', 'date'], var_name='name', value_name='value')

    df_emis_avg = df.copy().groupby(['date','name']).agg({'value': 'mean'}).reset_index()
    df_emis_avg['date'] = pd.to_datetime(df_emis_avg['date'])
    
    return df_emis_avg


# Filtrar los datos por país
def get_plot_emisiones_eu(pais, df):

    transf = {"Alemania":"DE",
              'Bélgica':"BE",
              'España':"ES",
              'Francia':"FR",
              'Italia':"IT",
              'Países bajos':"NL",
              'Portugal':"PT",
              'Reino unido':"GB"}


    chart = alt.Chart(df[df['name']== transf[pais]], title="Intensidad de carbono media diaria [gCO2eq/kWh]").mark_rect().encode(
        alt.X("date(date):O").title("Día").axis(format="%e", labelAngle=0),
        alt.Y("month(date):O").title("Mes"),
        alt.Color("value").title('gCO2eq/kWh').scale(
        domain=[0, 450, 900],
        range=['green', 'red', 'black']),
        tooltip=[
            alt.Tooltip("monthdate(date)", title="Fecha"),
            alt.Tooltip("value", title="Emisiones [gCO2eq/kWh]")]
    ).configure_view(
        step=13,
        strokeWidth=0
    ).configure_axis(
        domain=False
    ).properties(
    width=700,
    height=300
    )
    
    
    return chart



#####################################################
## Carga de datos
#####################################################

# Gráfico A.1: Generación por tecnologías
graf1_path = 'Datos/Generacion/GeneracionTotal_2023_h.csv'
df_gen = pd.read_csv(graf1_path, delimiter=';')

# Preprocesamiento
df_G1 = df_gen.copy()
df_G1 = prep_g1(df_G1)


# Gráfico A.3: Generación por tecnologias anual
df_G3 = df_gen.copy()
df_G3 = prep_g3(df_G3)


# Gráfico A.4: Generación por tecnologias mensual
df_G4 = df_gen.copy()
df_G4 = prep_g4(df_G4)


# Gráfico B.1: Desglose de precio horario
graf2_path = 'Datos/Economico/PrecioMedioHorarioFinal_2023_h.xlsx'
df_E_es = pd.read_excel(graf2_path)

df_B1 = df_E_es.copy()
df_B1 = prep_b1(df_B1)

# Gráfico B.2: Desglose de precio horario
graf3_path = 'Datos/Economico/PrecioEuropa_2023_h.csv'
df_E_eu = pd.read_csv(graf3_path, delimiter=';')

df_B2 = df_E_eu.copy()
df_B2 = prep_b2(df_B2)


# Gráfico C.1: Desglose de precio horario
graf4_path = 'Datos/Emisiones/output/CI_bottom_up_method.csv'
df_emis = pd.read_csv(graf4_path, delimiter=',')

df_emis_avg = prep_c1(df_emis)





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

st.title("Caso práctico de Visualización de Datos - Sector eléctrico español en 2023")
st.subheader('Visualización de datos - Curso 2023/2024')
st.subheader('Alumno: Javier Orive Soto')

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
        format="YYYY-MM-DD",
        key = 1
    )
   
    st.altair_chart(get_plot_generacion_dia(selected_date, df_G1), use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
         st.altair_chart(get_plot_generacion_dia_media(selected_date, df_G1))
    with col2:
        st.markdown('')
        st.markdown('')
        st.markdown('')
        st.markdown('')
        st.markdown('')
        st.markdown('')
        st.markdown('')
        with st.expander('Información sobre la página', expanded=True):
            st.write('''
            Esta página tiene por objetivo mostrar datos de generación eléctrica por tecnología de generación en España durante el año 2023.
            - Datos: [ESIOS de REE](https://www.esios.ree.es/es)
            - :orange[**Generación eléctrica por tecnología (diario)**]: muestra el mix eléctrico de un día de 2023 en España (con resolución por hora).
            - :orange[**Proporción de generación eléctrica media diaria por tecnología**]:  muestra la proporción diaria del mix eléctrico.
            - :orange[**Generación eléctrica anual por tecnología**]:  muestra la proporción anual del mix eléctrico por tecnologías.
            - :orange[**Generación eléctrica mensual por tecnología**]:  muestra la proporción mensual del mix eléctrico por tecnologías.         
            ''')
        
    col3, col4 = st.columns(2)
    
    with col3:
        st.altair_chart(get_plot_generacion_anual(df_G3))
    with col4:
        st.altair_chart(get_plot_generacion_mensual(df_G4))

with tab2:
    # Título
    st.header("Precio diario de la electricidad en España")
    
    start_date2 = dt.datetime(2023, 1, 1)
    end_date2 = dt.datetime(2023, 12, 31)
    selected_date2 = st.slider(
        'Seleccione una fecha',
        min_value=start_date2,
        max_value=end_date2,
        value=start_date2,
        format="YYYY-MM-DD",
        key = 2
    )

    colB1, colB2 = st.columns([0.8, 0.2], gap = "large")
    with colB1:
        st.altair_chart(get_plot_precio_hora(selected_date2, df_B1), use_container_width=True)
    with colB2:
        st.markdown('')
        st.markdown('')
        st.markdown('')
        st.markdown('')
        with st.expander('#### Resumen de precios:', expanded=True, icon = '💰'):
            a, b, c = prices(selected_date2, df_B1)
            st.metric(label="Medio diario", value='%.2f' % a +"€/MWh")
            st.metric(label="Mínimo diario", value='%.2f' % b +"€/MWh")
            st.metric(label="Máximo diario", value='%.2f' % c +"€/MWh")

    st.altair_chart(get_plot_precio_hora_eu(selected_date2, df_B2), use_container_width=True)
    
with tab3:
    # Título
    st.header("Emisiones de CO2 producidas para la generación de electricidad en la UE")
    st.write("")
    st.write("")
    
    colC1, colC2 = st.columns([0.15, 0.85], gap = "medium")
    with colC1:
    
        country = st.radio('Seleccione el país:',
                    ['Alemania','Bélgica','España','Francia','Italia','Países bajos','Portugal','Reino unido'])
    with colC2:
        st.altair_chart(get_plot_emisiones_eu(country, df_emis_avg), use_container_width=True)
    
    
with tab4:
    # Título
    st.header("Resumen del mercado electrico en España durante 2023")
    
    None
