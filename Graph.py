import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd

# Crear un DataFrame de ejemplo
data = {
    'x': [1, 2, 3, 4, 5],
    'y': [10, 11, 12, 13, 14]
}
df = pd.DataFrame(data)

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
