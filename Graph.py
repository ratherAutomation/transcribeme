import dash
from dash import dcc,html,Input,Output,dash_table
import plotly.express as px
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from datetime import date
import os
from io import StringIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import secrets
from pymongo import MongoClient

secret_file_path = '/etc/secrets/user'

# Verifica si el archivo existe
if os.path.exists(secret_file_path):
    # Abre y lee el contenido del archivo
    with open(secret_file_path, 'r') as file:
        username = file.read()
else:
    print("El secret file no existe o no se pudo leer.")

secret_file_path = '/etc/secrets/password'

# Verifica si el archivo existe
if os.path.exists(secret_file_path):
    # Abre y lee el contenido del archivo
    with open(secret_file_path, 'r') as file:
        password = file.read()

# Si el archivo no existe o no se pudo leer, maneja la situación de acuerdo a tus necesidades
else:
    print("El secret file no existe o no se pudo leer.")


uri = f"mongodb+srv://{username}:{password}@transcribeme.rletx0y.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Conectarse a la base de datos
db = client['TranscribeMe-charts']

# Obtener datos de la colección 'Income'
df_income = pd.DataFrame(list(db['Income'].find())).sort_values(by='date', ascending=True)

# Obtener datos de la colección 'Expenses'
expenses = pd.DataFrame(list(db['Expenses'].find()))

# Obtener datos de la colección 'subs-by-country'
subs_by_country_df = pd.DataFrame(list(db['subs-by-country'].find()))

# Obtener datos de la colección 'dau-by-country'
dau_by_country_df = pd.DataFrame(list(db['dau-by-country'].find()))

# Obtener datos de la colección 'new-users-by-country'
new_users_by_country = pd.DataFrame(list(db['new-users-by-country'].find())).sort_values(by='date', ascending=True)

# Calcular el ratio entre total de subscriptores y valor promedio de daily active users
ratio_df = pd.merge(
    dau_by_country_df.groupby('country')['user_ids'].mean().reset_index(),
    subs_by_country_df.groupby('country')['user_id'].sum().reset_index(),
    on='country',
    how='left'
)
ratio_df = ratio_df.rename(columns={'user_ids': 'dau', 'user_id': 'subscribers'})
ratio_df['subscribers'].fillna(0, inplace=True)
ratio_df['ratio'] = ratio_df['subscribers'] / ratio_df['dau']
ratio_df = ratio_df.round(1)

# Generar el DataFrame income_expenses_balance
onlycost_grouped = expenses.groupby(['date', 'country'])['cost'].sum().reset_index()
onlycost_grouped['date'] = onlycost_grouped['date'].apply(lambda x: str(x)[:10])
df_income['date'] = df_income['date'].apply(lambda x: str(x)[:10])
income_expenses_balance = pd.merge(
    onlycost_grouped,
    df_income,
    on=['country', 'date'],
    how='left'
)
income_expenses_balance['labels'] = income_expenses_balance['date'].apply(lambda x: str(x)[5:10])

# Calcular el balance por país
balance_by_country = income_expenses_balance.groupby('country').agg({
    'cost': 'mean',
    'expected_average_income': 'max'
}).reset_index()


# Crear una aplicación Dash
app = dash.Dash(__name__)
server = app.server


# Definir las opciones para el filtro desplegable de países
country_optioins = [{'label': country, 'value': country} for country in alltime_new_users['country'].unique()]

# Diseñar la interfaz de usuario de la aplicación
def alltime_dau():
    dau_by_date = dau_by_country_df.groupby(['date','country'])['user_ids'].sum().reset_index()
    
    fig = px.bar(
        dau_by_date,
        x='date',
        y='user_ids',
        color='country',
        labels={'user_ids': 'Daily Active Users', 'date': 'Date'},
        hover_data={'user_ids': ':.0f'}  # Formato con un decimal para la columna 'dau'
    )
    fig.update_layout(showlegend=False)

    return fig 
    
def alltime_new_users():
    new_users_by_date = new_users_by_country.groupby(['date','country'])['user_id'].sum().reset_index()
    
    fig = px.bar(
        new_users_by_date,
        x='date',
        y='user_id',
        color='country',
        labels={'user_id': 'New Users', 'date': 'Date'},
        hover_data={'user_id': ':.0f'}  # Formato con un decimal para la columna 'dau'
    )
    fig.update_layout(showlegend=False)
    
    return fig
def alltime_subs():
    subs_by_date = subs_by_country_df.groupby(['start_date','country'])['user_id'].sum().reset_index()
    
    fig = px.bar(
        subs_by_date,
        x='start_date',
        y='user_id',
        color='country',
        labels={'user_id': 'Subs By Date', 'start_date': 'Date'},
        hover_data={'user_id': ':.0f'}  # Formato con un decimal para la columna 'dau'
    )
    fig.update_layout(showlegend=False)
    
    return fig


def all_income_graph():

    income_by_week_country = df_income.groupby(['week','country'])['expected_average_income'].sum().reset_index()
    fig = px.bar(
        income_by_week_country[(income_by_week_country['week']>35)&(income_by_week_country['week']<45)],
        x='week',
        y='expected_average_income',
        color='country',
        labels={'expected_average_income': 'Expected Income', 'week': 'Week'},
        hover_data={'expected_average_income': ':.0f'}  # Formato con un decimal para la columna 'dau'
    )
    return fig
    
def all_expenses_graph():
    expenses_by_week_country = expenses.groupby(['week','country'])['cost'].sum().reset_index()
    fig = px.bar(
        expenses_by_week_country[expenses_by_week_country['week']>35],
        x='week',
        y='cost',
        color='country',
        labels={'cost': 'Costs', 'week': 'Week'},
        hover_data={'cost': ':.0f'}  # Formato con un decimal para la columna 'dau'
    )
    return fig

def figura_grafico_dispersion():
    fig = px.scatter(
        ratio_df,
        x='dau',
        y='subscribers',
        color='country',
        labels={'dau': 'Daily Active Users', 'subscribers': 'Total Subscribers'},
        hover_data={'dau': ':.1f'}  # Formato con un decimal para la columna 'dau'
    )  
    # Filtrar los países cuyo valor de 'subscribers' esté por encima de 200
    paises_con_subscribers_altos = ratio_df[ratio_df['subscribers'] > 150]
    # Agregar etiquetas de texto para los países con 'subscribers' altos
    for i, row in paises_con_subscribers_altos.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row['dau']],
                y=[row['subscribers']],
                text=[row['country']],
                mode='text',
                textfont=dict(color='black', size=10),
                textposition='top left',  # Ubicación del texto (derecha y arriba)    
                showlegend=False
            )
        ) 
        
        fig.update_traces(showlegend=False)
        fig.update_xaxes(type='log')
        fig.update_layout(
            xaxis=dict(
                showline=True,  # Mostrar la línea del eje x
                linecolor='black',  # Color de la línea del eje x (negro)
                linewidth=1,  # Ancho de la línea del eje x (delgado)
                showgrid=True,  # Mostrar líneas de cuadrícula en el eje x
                gridcolor='lightgray',  # Color de las líneas de cuadrícula (gris claro)
                gridwidth=0.5  # Ancho de las líneas de cuadrícula (fino)
            ),
            plot_bgcolor='white',  # Fondo del gráfico
            paper_bgcolor='white'  # Fondo del papel (todo el gráfico)
        )

    return fig
    
columnas_personalizadas = [
    {'name': 'Country', 'id': 'country'},
    {'name': 'Average DAU', 'id': 'dau'},
    {'name': 'Sub', 'id': 'subscribers'},
    {'name': 'Ratio', 'id': 'ratio'}
]
tabla_de_datos = dash_table.DataTable(
    id='tabla-de-datos',
    columns=columnas_personalizadas,
    data=ratio_df.to_dict('records'),
    fixed_rows={'headers': True},
    
    style_cell={'minWidth': 60, 'maxWidth': 100},
    style_table={'height': '350px', 'overflowY': 'auto','padding-top': '50px'},  # Limitar la altura de la tabla y agregar scroll
    sort_action='native',  # Habilitar la capacidad de ordenar la tabla

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
#All time
    html.Div([
        # Columna izquierda (para el primer gráfico futuro)
        html.Div([
            html.H3('DAU By Date'),
            dcc.Graph(id='all-time-dau-average', figure=alltime_dau())
        ], style={'width': '33%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades
                
        # Columna derecha (para el segundo gráfico futuro)
        html.Div([
            html.H3('New Users By Date'),
            dcc.Graph(id='all-time-new-users', figure=alltime_new_users())

        ], style={'width': '33%', 'display': 'inline-block'}),
        html.Div([
            html.H3('New Subs By Date'),
            dcc.Graph(id='all-time-subs', figure=alltime_subs())

        ], style={'width': '33%', 'display': 'inline-block'}),        
        
    ], style={'width': '100%', 'display': 'flex'}),  # Ajusta el ancho según tus necesidades    
    
    
    
    html.Div([# Gráfico central (puedes personalizar esto)
        dcc.Dropdown(
            id='country-filter',
            options=country_optioins,
            value='Argentina',  # País seleccionado por defecto
            multi=False
        ),
        dcc.Graph(id='new-subs-by-country'),
        dcc.Graph(id='dau-by-country')
    ], style={'width': '90%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades

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
        html.H1("General balances"),
        html.Div([
            # Columna izquierda (para el primer gráfico futuro)
            html.Div([
                html.H3('daily cost/daily expected income | from date 01/09'),
                dcc.Graph(id='graph')
            ], style={'width': '50%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades
            html.Div([
                html.H3('average daily income vs expected daily income for all countries'),
                dcc.Graph(id='graph-2')      
            ], style={'width': '50%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades
        ], style={'width': '100%', 'display': 'inline-block'}),
    ], style={'width': '100%', 'display': 'inline-block'}),   

    
    html.Div([
        html.H1("Gráfico de gastos e ingreso por pais"),
        dcc.Graph(id='graph3')
    ], style={'width': '100%', 'display': 'inline-block'}),
    
    html.Div([
        html.H1("Incomes and Expenses"),
        html.Div([
            # Columna izquierda (para el primer gráfico futuro)
            html.Div([
                html.H3('Expenses'),
                dcc.Graph(id='expenses_general',figure=all_expenses_graph())
            ], style={'width': '50%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades
            html.Div([
                html.H3('Income'),
                dcc.Graph(id='income_general',figure=all_income_graph())      
            ], style={'width': '50%', 'display': 'inline-block'}),  # Ajusta el ancho según tus necesidades
        ], style={'width': '100%', 'display': 'inline-block'}),
    ], style={'width': '100%', 'display': 'inline-block'}),   

])   

@app.callback(
    dash.dependencies.Output('new-subs-by-country', 'figure'),
    dash.dependencies.Output('dau-by-country','figure'),
    [dash.dependencies.Input('country-filter', 'value')]
)
def actualizar_grafico(selected_country):
    # Filtrar los datos por el país seleccionado
    df_filtrado = subs_by_country_df[subs_by_country_df['country'] == selected_country]
    dau_df_filtered = dau_by_country_df[dau_by_country_df['country'] == selected_country]
    filtered_new_users_by_country_df = new_users_by_country[new_users_by_country['country'] == selected_country]

    # Crear gráficos de barras

    color_barra = '#1da453'

    fig = px.bar(df_filtrado, x='start_date', y='user_id', title=f'New subs & daily active users by date in {selected_country}', color_discrete_sequence=[color_barra])
    dau_by_country_fig=make_subplots(specs=[[{"secondary_y": True}]])
    
    #dau_by_country_fig = px.bar(dau_df_filtered,x='date',y='user_ids', color_discrete_sequence=[color_barra])
    
    # Agregar una línea vertical discontinua en la fecha 2023-09-13 con un título
    fecha_cambio = '2023-09-13'
    fig.add_shape(
        go.layout.Shape(
            type="line",
            x0=fecha_cambio,
            x1=fecha_cambio,  
            y0=0,
            y1=max(df_filtrado['user_id']),
            line=dict(color="grey", width=2, dash='dash'),
        )
    )
    
    fig.add_annotation(
        go.layout.Annotation(
            text="3 days free trial",
            x=fecha_cambio,
            y=max(df_filtrado['user_id']),
            showarrow=True,
            arrowhead=1,
            ax=-50,
            ay=-30
        )
    )
    # Personalizar el diseño del gráfico
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='New Subscribers',
        showlegend=False,  # Para ocultar la leyenda si no se necesita
        plot_bgcolor='white',  # Fondo blanco
        paper_bgcolor='white',  # Fondo del papel (todo el gráfico)
        xaxis=dict(
            linecolor='black',  # Color de la línea del eje x (negro)
            linewidth=1  # Ancho de la línea del eje x (delgado)
        ),
        yaxis=dict(
            linecolor='black',  # Color de la línea del eje y (negro)
            linewidth=1  # Ancho de la línea del eje y (delgado)
        )
    )

    #dau by country figure

    dau_by_country_fig.add_trace(
        go.Bar(x=dau_df_filtered['date'],y=dau_df_filtered['user_ids'], name="dau"),
        secondary_y=False,
    )
    dau_by_country_fig.add_trace(
        go.Scatter(x=filtered_new_users_by_country_df['date'], y=filtered_new_users_by_country_df['user_id'], name="new users"),
        secondary_y=True,
    )
    
    dau_by_country_fig.add_shape(
        go.layout.Shape(
            type="line",
            x0=fecha_cambio,
            x1=fecha_cambio,  
            y0=0,
            y1=max(dau_df_filtered['user_ids']),
            line=dict(color="grey", width=2, dash='dash'),
        )
    )    
    dau_by_country_fig.update_layout(
        xaxis_title='Date',
        #yaxis_title='DAU',
        #showlegend=False,  # Para ocultar la leyenda si no se necesita
        plot_bgcolor='white',  # Fondo blanco
        paper_bgcolor='white',  # Fondo del papel (todo el gráfico)
        xaxis=dict(
            linecolor='black',  # Color de la línea del eje x (negro)
            linewidth=1  # Ancho de la línea del eje x (delgado)
        ),
        yaxis=dict(
            linecolor='black',  # Color de la línea del eje y (negro)
            linewidth=1  # Ancho de la línea del eje y (delgado)
        )
    )
    dau_by_country_fig.update_yaxes(title_text="<b>dau</b>", secondary_y=False)
    dau_by_country_fig.update_yaxes(title_text="<b>new users</b>", secondary_y=True)
    return fig,dau_by_country_fig



@app.callback(
    Output('graph3', 'figure'),
    Input('country-filter', 'value')
)
def update_graph_2(selected_country):
    filtered_df = expenses[expenses['country'] == selected_country]
    filtered_income_df = df_income[df_income['country'] == selected_country]
    colors = {
        'wpp_price': '#00a985',
        'tkn_price': 'darkgray',
        'whisper_price': '#51da48'
        # Agrega más cost_type y colores si es necesario
    }
       
    
    fig = px.bar(
        filtered_df,
        x='date',
        y='cost',
        color='cost_type',
        color_discrete_map=colors,       
        title=f'associeted costs and expected revenue for: {selected_country}',
        labels={'Service': 'Valor del Servicio'},
    )
    fig.add_trace(go.Scatter(
        x=filtered_income_df['date'],
        y=filtered_income_df['expected_average_income'],
        mode='lines',
        name='daily_expected_income',
        line=dict(color='black'),  # Personaliza el color de la línea
    ))
    fig.update_layout(plot_bgcolor='white')
    
    return fig


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
        title=f'Expenses and Expected Income for: {selected_country}'
    )

    fig.update_traces(
        text=filtered_df['labels'],
        hovertemplate='<b>Date</b>: %{text}<br><b>Cost</b>: %{x}<br><b>Expected Avg Income</b>: %{y}',  # Posición y tamaño de las etiquetas
    )
    fig.add_trace(
        go.Scatter(
            x=income_expenses_balance['cost'],
            y=1 * income_expenses_balance['cost'],
            mode='lines',
            name='y = x',
            line=dict(color='black', dash='dash')
        )
    )
            
    max_axis_val = max([filtered_df['cost'].max(),filtered_df['expected_average_income'].max()])*1.1
    fig.update_xaxes(range=[0, max_axis_val])
    fig.update_yaxes(range=[0, max_axis_val])

    return fig

@app.callback(
    Output('graph-2', 'figure'),
    Input('country-filter', 'value')
)
def update_balance_graph(selected_country):
    fig = px.scatter(
        balance_by_country,
        x='cost',
        y='expected_average_income',
        title= 'Associeted costs and expected revenue all countries',
        color='country',
        labels={'cost': 'average daily cost', 'expected_average_income': 'current daily income'},
    )
    fig.update_traces(showlegend=False)

    fig.update_layout(
        xaxis=dict(
            showline=True,  # Mostrar la línea del eje x
            linecolor='black',  # Color de la línea del eje x (negro)
            linewidth=1,  # Ancho de la línea del eje x (delgado)
            showgrid=True,  # Mostrar líneas de cuadrícula en el eje x
            gridcolor='lightgray',  # Color de las líneas de cuadrícula (gris claro)
            gridwidth=0.5  # Ancho de las líneas de cuadrícula (fino)
        ),
            plot_bgcolor='white',  # Fondo del gráfico
            paper_bgcolor='white'  # Fondo del papel (todo el gráfico)
    )
    fig.add_trace(
        go.Scatter(
            x=balance_by_country['cost'],
            y=1 * balance_by_country['cost'],
            mode='lines',
            name='x=y',
            line=dict(color='black', dash='dash')
        )
    )    
    return fig

    
# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
