import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
# Leer los CSV y reconstruir el DataFrame original
split1_read = pd.read_csv('ipc_division_part_1.csv', parse_dates=['Fecha'])
split2_read = pd.read_csv('ipc_division_part_2.csv', parse_dates=['Fecha'])
split3_read = pd.read_csv('ipc_division_part_3.csv', parse_dates=['Fecha'])
split4_read = pd.read_csv('ipc_division_part_4.csv', parse_dates=['Fecha'])
split5_read = pd.read_csv('ipc_division_part_5.csv', parse_dates=['Fecha'])
split6_read = pd.read_csv('ipc_division_part_6.csv', parse_dates=['Fecha'])

ipc_division = pd.concat([split1_read, split2_read, split3_read,
                          split4_read,split5_read,split6_read], ignore_index=True)

ipc_general = pd.read_csv('ipc_general_100.csv', parse_dates=['Fecha'])
#ipc_division = pd.read_csv('ipc_division_100.csv', parse_dates=['Fecha'])
ponderaciones = pd.read_csv("ponderaciones.csv")


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Inflación en Bolivia"),
    html.H2("Medición del Índice de Precios al Consumidor (IPC)"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Región:"),
            dcc.Dropdown(
                id="dropdown-lugar",
                options=[{"label": lugar, "value": lugar_id} for lugar, lugar_id in 
                         zip(ipc_general['LUGAR_LABEL'].unique(), ipc_general['LUGAR_ID_STR'].unique())],
                value=1001,  # Valor predeterminado
                placeholder="Seleccione un lugar",
            ),
        ], width=6),

        dbc.Col([
            html.Label("Seleccione Mes Base:"),
            dcc.Dropdown(
                id="dropdown-mes-base",
                options=[{"label": mes_base, "value": mes_base_id} for mes_base, mes_base_id in 
                         zip(ipc_general['MES_BASE_LABEL'].unique(), ipc_general['MES_BASE_STR'].unique())],
                value=2008.03,  # Valor predeterminado
                placeholder="Seleccione un mes base",
            ),
        ], width=6),
    ]),

    dbc.Row([
        dcc.Markdown(
            """        
            #### Método de medición mes base = 100 
            Se escoge una región en un mes para que ese nivel de precios sea igual a 100 
            el siguiente mes será la variación % en los precios por 100. 
            Ejm. si el valor del mes siguiente es 110 por tanto los precios se incrementaron un 10% con respecto al mes base.
            """
        ),
        dbc.Alert(id="alerta-mes-base", color="warning"),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-general"), width=12),
    ]),
    dbc.Row([
        dcc.Markdown(
            """        
            #### Categorías que conforman el IPC 
            """
        )
    ]),
    dbc.Row([
        dbc.Col(
            html.Img(
                src="assets/IPC_donut_chart.png",
                style={
                    "width": "100%",   
                    "height": "auto", 
                    "display": "block",
                    "margin": "0 auto", 
                },
            )
        )
    ]),
    html.Br(),
    
    # Nuevo Dropdown y Gráfico
    dbc.Row([
            dcc.Markdown(
            """        
            #### Ponderación de productos dentro de una categoría 
            """
        ),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': str(i), 'value': i} for i in ponderaciones['categoria_name'].unique()],
            value=ponderaciones['categoria_name'].unique()[0],  
            style={'width': '50%'}
        ),
        dbc.Col(dcc.Graph(id="bar-chart"), width=12),
    ]),

    html.Br(),
    dbc.Row([
        dcc.Markdown(
            """        
            #### Variación de precios por categoría 
            """
        )
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="grafico-division"), width=12),
    ])
])

@app.callback(
    Output("grafico-general", "figure"),
    Output("grafico-division", "figure"),
    Output("alerta-mes-base", "children"),
    Input("dropdown-lugar", "value"),
    Input("dropdown-mes-base", "value")
)
def actualizar_graficos(lugar_id_str, mes_base_str):
    # Filtrado de datos
    ipc_general_filtrado = ipc_general[
        (ipc_general["LUGAR_ID_STR"] == lugar_id_str) & (ipc_general["MES_BASE_STR"] == mes_base_str)
    ]
    
    ipc_division_filtrado = ipc_division[
        (ipc_division["LUGAR_ID_STR"] == lugar_id_str) & (ipc_division["MES_BASE_STR"] == mes_base_str)
    ]
    
    # Obtener el nombre del mes base seleccionado y descomponerlo en mes y año
    mes_base_label = ipc_general.loc[ipc_general['MES_BASE_STR'] == mes_base_str, 'MES_BASE_LABEL'].iloc[0]
    año, mes = mes_base_label.split('.')  # Divide en mes y año
    lugar_id_str_name = ipc_general_filtrado['LUGAR_LABEL'].iat[0]
    # Diccionario para convertir el número del mes a nombre en español
    meses_es = {
        "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
        "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
        "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
    }
    mes_nombre = meses_es.get(mes.zfill(2), mes)  # Obtén el nombre del mes
    # Crear el diccionario de mapeo
    division_mapping = {
        11: "Alimentos y bebidas consumidos fuera del hogar", 
        1: "Alimentos y bebidas no alcohólicas", 
        2: "Bebidas alcohólicas y tabaco", 
        12: "Bienes y servicios diversos", 
        8: "Comunicaciones", 
        10: "Educación", 
        5: "Muebles, bienes y servicios domésticos", 
        3: "Prendas de vestir y calzado", 
        9: "Recreación y cultura", 
        6: "Salud", 
        7: "Transporte", 
        4: "Vivienda y servicios básicos", 
        0: "ÍNDICE GENERAL"
        }
    ipc_division_filtrado['DIVISION_LABEL'] = ipc_division_filtrado['DIVISION_ID'].map(division_mapping)

    # Gráfico 1: Valor vs Fecha en ipc_general con rangeslider
    fig_general = px.line(ipc_general_filtrado, x="Fecha", y="VALOR",
                          title=f"Variación de Precios en {lugar_id_str_name}",
                          labels={"VALOR": f"IPC = 100 para {mes_nombre} de {año}"})
    fig_general.update_xaxes(
        rangeslider_visible=True,
        range=["2008-01-01", "2020-12-31"])  # Agrega rangeslider
    
    fig_general.add_shape(
        type="line",
        x0=ipc_general_filtrado['Fecha'].min(),
        y0=100,
        x1=ipc_general_filtrado['Fecha'].max(),
        y1=100,
        line=dict(color="orange", width=2, dash="dash")
    )
    
    # Gráfico 2: Valor vs Fecha en ipc_division con línea de color por DIVISION_LABEL y rangeslider
    color_map_div = {
        'Alimentos y bebidas no alcohólicas': "#F95738",
        'Bebidas alcohólicas y tabaco': "#FFE646",
        'Prendas de vestir y calzado': "#FDB1CD",
        'Vivienda y servicios básicos': "#AEE52C",
        'Muebles. bienes y servicios domésticos': "#A2498F",
        'Salud': "#4AC6DB",
        'Transporte': "#214869",
        'Comunicaciones': "#216869",
        'Recreación y cultura': "#512D38",
        'Educación': "#229D74",
        'Alimentos y bebidas consumidos fuera del hogar': "#E3BD3E",
        'Bienes y servicios diversos': "#D3D0CB"
    }

    fig_division = px.line(
        ipc_division_filtrado,
        x="Fecha",
        y="VALOR",
        color="DIVISION_LABEL",
        color_discrete_map=color_map_div,  # Mapeo de colores específico
        title="",
        labels={"DIVISION_LABEL": "",
                "VALOR":f"IPC por Categorías en {lugar_id_str_name}"},  # Ocultar el nombre de la columna en la leyenda
        height=800
    )
    fig_division.update_xaxes(rangeslider_visible=True)  # Agrega rangeslider
    
    # Ajustar la leyenda en la parte superior
    fig_division.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    ))
    
    # Hacer que la mitad de las líneas estén invisibles por defecto
    division_labels = ipc_division_filtrado['DIVISION_LABEL'].unique()
    visible_list = ['legendonly' if i >= len(division_labels) / 2 else True for i in range(len(division_labels))]
    for trace, visibility in zip(fig_division.data, visible_list):
        trace.visible = visibility
    
    # Actualizar el texto de la alerta con el mes base seleccionado
    texto_alerta = f"Los precios de {mes_nombre} de {año} son = 100"
    
    return fig_general, fig_division, texto_alerta

@app.callback(
    Output('bar-chart', 'figure'),
    [Input('category-dropdown', 'value')]
)
def update_graph(selected_category):
    # Filtrar el DataFrame por la categoría seleccionada y head_cat == 0
    df_filtered = ponderaciones[(ponderaciones['categoria_name'] == selected_category) & (ponderaciones['head_cat'] == 0)]
    
    # Ordenar por ponderación de mayor a menor
    df_filtered = df_filtered.sort_values(by='ponderacion', ascending=False)
    
    if df_filtered.shape[0] > 18 :
        top_15 = df_filtered.head(18)
        others = df_filtered.iloc[18:]
        others_sum = others['ponderacion'].sum()
        num_filas = others.shape[0]
        num_filas
        others_sum = round(others['ponderacion'].sum(),2)
        others_categoria = others['categoria'].iat[0]    

        others_df = pd.DataFrame({
            'producto': [f'Resto:Otros {num_filas} productos con menor ponderación'],
            'ponderacion': [others_sum],
            'categoria' : [others_categoria],
            'head_cat' : [1],
            'categoria_name' : [selected_category]
            })
        final_df = pd.concat([top_15, others_df], ignore_index=True)
    else:
        final_df = df_filtered
        
    # Acortar nombres de los productos
    #final_df['producto'] = final_df['producto'].apply(lambda x: ' '.join(x.split()[:3]))

     # Crear un diccionario para mapear colores según categoria_name
    color_map = {
     'Alimentos y Bebidas No Alcohólicas': "#F95738",
     'Bebidas Alcohólicas y Tabaco': "#FFE646",
     'Prendas de Vestir y Calzado': "#FDB1CD",
     'Vivienda y Servicios Básicos': "#AEE52C",
     'Muebles. Bienes y Servicios Domésticos': "#A2498F",
     'Salud': "#4AC6DB",
     'Transporte': "#214869",
     'Comunicaciones': "#216869",
     'Recreación y Cultura': "#512D38",
     'Educación': "#229D74",
     'Alimentos y Bebidas Consumidos Fuera del Hogar': "#E3BD3E",
     'Bienes y Servicios Diversos': "#D3D0CB"
        }
    
    # Crear el gráfico de barras
    fig = px.bar(final_df, 
                 y='producto', 
                 x='ponderacion', 
                 orientation='h',  # Hacer las barras horizontales
                 title=f'Productos en la categoría {selected_category}',
                 labels={'ponderacion': 'Producto en (%) del IPC Global',
                         'producto' : ""},
                 color = 'categoria_name',
                 color_discrete_map = color_map,
                 height=600)
    
    fig.update_traces(
    text=final_df['ponderacion'],  # El texto a mostrar
    textposition='outside',        # Posición del texto (puede ser 'inside', 'outside', etc.)
    textfont=dict(size=10)         # Tamaño del texto
)
    
    fig.update_layout(
    xaxis=dict(range=[0, 10]),
    yaxis=dict(
        categoryorder="array",
        categoryarray=final_df['producto'][::-1].tolist(),  # Orden invertido
        tickfont=dict(size=10)  # Tamaño de la fuente de los nombres de los productos
    ),
    showlegend=False  # Quitar la leyenda
)

    
    return fig

if __name__ == "__main__":
    app.run_server(debug=True,
     host='0.0.0.0'
     )