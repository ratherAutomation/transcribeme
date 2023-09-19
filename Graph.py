import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import requests
from io import StringIO

# URL cruda del archivo CSV en GitHub (reemplaza con la URL de tu archivo)
url_csv_raw = 'https://raw.githubusercontent.com/ratherAutomation/transcribeme/main/mi_archivo.csv'

# Hacer una solicitud HTTP para obtener el contenido del archivo CSV
response = requests.get(url_csv_raw)
print(response.text)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Leer el contenido del archivo CSV en un DataFrame
    df = pd.read_csv(StringIO(response.text))
    print(df)
else:
    print("No se pudo obtener el archivo CSV")

# Crear una aplicación Dash
app = dash.Dash(__name__)
server = app.server
# Definir el diseño de la aplicación
app.layout = html.Div([
    html.H1("Gráfico de Prueba"),
    dcc.Graph(
        id='grafico-prueba',
        figure=px.scatter(df, x='x', y='y', title='Gráfico de dispersión de prueba')
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
