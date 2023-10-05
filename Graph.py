import dash
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import dash_table
import plotly.express as px
import pandas as pd
import requests
import os
from io import StringIO
import plotly.graph_objects as go

from pymongo import MongoClient

# URL cruda del archivo CSV en GitHub (reemplaza con la URL de tu archivo)
url_csv_raw = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/recent_subs.csv'
url_csv_dau_sub = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/ratio_df.csv'
url_csv_balance = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/income_expense_balance.csv'
url_csv_all_costs = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/all_cost.csv'

username=os.environ.get('user')
password =os.environ.get('password')
uri = f"mongodb+srv://{username}:{password}@transcribeme.rletx0y.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
db = client['TranscribeMe-charts']  # Reemplaza 'nombre_de_tu_base_de_datos' con el nombre de tu base de datos
collection = db['Income']
data_from_mongodb = list(collection.find())
# Paso 4: Convierte los datos en un DataFrame
income = income.DataFrame(data_from_mongodb)


                  
# Hacer una solicitud HTTP para obtener el contenido del archivo CSV
response = requests.get(url_csv_raw)
# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Leer el contenido del archivo CSV en un DataFrame
    recent_subs = pd.read_csv(StringIO(response.text))
else:
    print("No se pudo obtener el archivo CSV")

response_two = requests.get(url_csv_dau_sub)
if response_two.status_code == 200:
    ratio_df = pd.read_csv(StringIO(response_two.text))
else:
    print("No se pudo obtener el archivo CSV")
    
response_three = requests.get(url_csv_balance)
if response_three.status_code == 200:
    # Leer el contenido del archivo CSV en un DataFrame
    income_expenses_balance = pd.read_csv(StringIO(response_three.text))
else:
    print("No se pudo obtener el archivo CSV")

response_allcost = requests.get(url_csv_balance)
if response_allcost.status_code == 200:
    # Leer el contenido del archivo CSV en un DataFrame
    all_costs = pd.read_csv(StringIO(response_allcost.text))
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

tabla_de_income = dash_table.DataTable(
        id='tabla-de-income',
        columns=[
            {"name": col, "id": col} for col in df_income.columns
        ],
        data=df_income.to_dict('records'),
        style_cell={'minWidth': 60, 'maxWidth': 100},
        style_table={'height': '300px', 'overflowY': 'auto'},
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
   
    html.Div([
        html.H1("balance"),
        dcc.Dropdown(
            id='country-filter',
            options=[{'label': country, 'value': country} for country in income_expenses_balance['country'].unique()],
            value=income_expenses_balance['country'].unique()[0]  # Valor predeterminado
        ),
        dcc.Graph(id='graph')
    ], style={'width': '100%', 'display': 'inline-block'}),
    html.Div([
        html.H3('income by country'),
            tabla_de_income
        ], style={'width': '100%', 'display': 'inline-block'})
])   
    
@app.callback(
    Output('graph', 'figure'),
    Input('country-filter', 'value')
)
def update_graph(selected_country):
    filtered_df = income_expenses_balance[income_expenses_balance['country'] == selected_country]
    fig = px.scatter(
        filtered_df,
        x='cost',
        y='expected_average_income',
        title=f'associeted costs and expected revenue for: {selected_country}'
    ) 
    
    fig.update_traces(
        text=filtered_df['labels'],
        hovertemplate='<b>Date</b>: %{text}<br><b>Cost</b>: %{x}<br><b>Expected Avg Income</b>: %{y}',  # Posición y tamaño de las etiquetas
    )
    fig.add_trace(
        go.Scatter(
            x=income_expenses_balance['cost'],  # Puedes ajustar estos valores según tu necesidad
            y=1 * income_expenses_balance['cost'],  # Pendiente de 0.05
            mode='lines',
            name='y = x',  # Nombre de la recta en la leyenda
            line=dict(color='black', dash='dash')  # Personalizar el estilo de la línea
        )
    )
            
    max_axis_val = max([filtered_df['cost'].max(),filtered_df['expected_average_income'].max()])*1.1
    fig.update_xaxes(range=[0, max_axis_val]) #filtered_df['cost'].min()
    fig.update_yaxes(range=[0, max_axis_val]) #filtered_df['expected_average_income'].min()
    
    return fig
        
    
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
