import dash
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import dash_table
import plotly.express as px
import pandas as pd
import requests
from io import StringIO
import plotly.graph_objects as go

# URL cruda del archivo CSV en GitHub (reemplaza con la URL de tu archivo)
url_csv_raw = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/subs_sixty.csv'
url_csv_dau_sub = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/ratio_df.csv'

# Hacer una solicitud HTTP para obtener el contenido del archivo CSV
response = requests.get(url_csv_raw)
# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Leer el contenido del archivo CSV en un DataFrame
    recent_subs = pd.read_csv(StringIO(response.text))
else:
    print("No se pudo obtener el archivo CSV")
# Hacer una solicitud HTTP para obtener el contenido del archivo CSV
response_two = requests.get(url_csv_dau_sub)
# Verificar si la solicitud fue exitosa
if response_two.status_code == 200:
    # Leer el contenido del archivo CSV en un DataFrame
    ratio_df = pd.read_csv(StringIO(response_two.text))
else:
    print("No se pudo obtener el archivo CSV")


# Crear una aplicación Dash
app = dash.Dash(__name__)
server = app.server


# Definir las opciones para el filtro desplegable de países
opciones_paises = [{'label': pais, 'value': pais} for pais in recent_subs['country'].unique()]

# Diseñar la interfaz de usuario de la aplicación

def figura_grafico_dispersion():
    # ... Código para el segundo gráfico de dispersión (estático) ...
    fig = px.scatter(
        ratio_df,
        x='average_dau',
        y='total_subs',
        color='country',
        labels={'dau': 'DAU', 'new_subscribers': 'New Subscribers'},
        
    )
    fig.update_traces(showlegend=False)

    return fig
columnas_personalizadas = [
    {'name': 'Country', 'id': 'country'},
    {'name': 'Average DAU', 'id': 'average_dau'},
    {'name': 'Sub', 'id': 'total_subs'},
    {'name': 'Ratio', 'id': 'ratio'}
]
tabla_de_datos = dash_table.DataTable(
    id='tabla-de-datos',
    columns=columnas_personalizadas,
    data=ratio_df.to_dict('records'),
    fixed_rows={'headers': True},
    
    style_cell={'minWidth': 60, 'maxWidth': 100},
    style_table={'height': '350px', 'overflowY': 'auto','padding-top': '50px'}  # Limitar la altura de la tabla y agregar scroll
)



app.layout = html.Div([
    # División principal con dos partes: gráfico central y división de dos columnas
    html.Div([# Gráfico central (puedes personalizar esto)
        dcc.Dropdown(
        id='filtro-pais',
        options=opciones_paises,
        value='Argentina',  # País seleccionado por defecto
        multi=False
    ),
        dcc.Graph(id='grafico-nuevos-subscriptores')
    ], style={'width': '100%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades

    # División de dos columnas (para futuros gráficos)
    html.Div([
        # Columna izquierda (para el primer gráfico futuro)
        html.Div([
            html.H3('Avg DAU vs New Subs Ratio'),
            dcc.Graph(id='grafico-dispersion', figure=figura_grafico_dispersion())
        ], style={'width': '60%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades
                
        # Columna derecha (para el segundo gráfico futuro)
        html.Div([
            html.H3('Ratio by country'),
            tabla_de_datos
        ], style={'width': '40%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades
    ], style={'width': '100%', 'display': 'flex'}),  # Ajusta el ancho según tus necesidades
])


# Definir la función de actualización del gráfico
@app.callback(
    dash.dependencies.Output('grafico-nuevos-subscriptores', 'figure'),
    [dash.dependencies.Input('filtro-pais', 'value')]
)
def actualizar_grafico(pais_seleccionado):
    # Filtrar los datos por el país seleccionado
    df_filtrado = recent_subs[recent_subs['country'] == pais_seleccionado]

    # Crear el gráfico de barras
    fig = px.bar(df_filtrado, x='date', y='new_subs', title=f'Nuevos Subscriptores por Fecha en {pais_seleccionado}')

    # Agregar una línea vertical discontinua en la fecha 2023-09-13 con un título
    fecha_cambio = '2023-09-13'
    fig.add_shape(
        go.layout.Shape(
            type="line",
            x0=fecha_cambio,
            x1=fecha_cambio,
            y0=0,
            y1=max(df_filtrado['new_subs']),
            line=dict(color="grey", width=2, dash='dash'),
        )
    )

    # Agregar un título a la línea vertical
    fig.add_annotation(
        go.layout.Annotation(
            text="3 days free trial",
            x=fecha_cambio,
            y=max(df_filtrado['new_subs']),
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
