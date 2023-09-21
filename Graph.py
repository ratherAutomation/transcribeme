import dash
from dash import dcc
from dash import html
from dash import Input
from dash import Output
import plotly.express as px
import pandas as pd
import requests
from io import StringIO

# URL cruda del archivo CSV en GitHub (reemplaza con la URL de tu archivo)
url_csv_raw = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/subs_sixty.csv'

# Hacer una solicitud HTTP para obtener el contenido del archivo CSV
response = requests.get(url_csv_raw)
# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Leer el contenido del archivo CSV en un DataFrame
    recent_subs = pd.read_csv(StringIO(response.text))
else:
    print("No se pudo obtener el archivo CSV")

# Crear una aplicación Dash
app = dash.Dash(__name__)
server = app.server

# Definir las opciones para el filtro desplegable de países
opciones_paises = [{'label': pais, 'value': pais} for pais in recent_subs['Country'].unique()]

# Diseñar la interfaz de usuario de la aplicación
app.layout = html.Div([
    dcc.Dropdown(
        id='filtro-pais',
        options=opciones_paises,
        value='Argentina',  # País seleccionado por defecto
        multi=False
    ),
    dcc.Graph(id='grafico-nuevos-subscriptores')
])

# Definir la función de actualización del gráfico
@app.callback(
    dash.dependencies.Output('grafico-nuevos-subscriptores', 'figure'),
    [dash.dependencies.Input('filtro-pais', 'value')]
)
def actualizar_grafico(pais_seleccionado):
    # Filtrar los datos por el país seleccionado
    df_filtrado = recent_subs[recent_subs['Country'] == pais_seleccionado]

    # Crear el gráfico de barras
    fig = px.bar(df_filtrado, x='date', y='new_subscribers', title=f'Nuevos Subscriptores por Fecha en {pais_seleccionado}')

    # Agregar una línea vertical en la fecha 2023-09-13
    fecha_cambio = '2023-09-13'
    fig.add_shape(
        go.layout.Shape(
            type="line",
            x0=fecha_cambio,
            x1=fecha_cambio,
            y0=0,
            y1=max(df_filtrado['new_subscribers']),
            line=dict(color="black", width=4,dash='dash'),
        )
    )
    fig.add_annotation(
        go.layout.Annotation(
            text="3 days free trial",
            x=fecha_cambio,
            y=max(df_filtrado['new_subscribers']),
            showarrow=True,
            arrowhead=1,
            ax=-50,
            ay=-30
        )
    )
    # Personalizar el diseño del gráfico
    fig.update_layout(
        xaxis_title='Fecha',
        yaxis_title='Nuevos Subscriptores',
        showlegend=False  # Para ocultar la leyenda si no se necesita
    )

    return fig

# Ejecutar la aplicación

if __name__ == '__main__':
    app.run_server(debug=True)
