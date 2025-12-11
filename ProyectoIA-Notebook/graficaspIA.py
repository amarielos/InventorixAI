#Estandarizamos los datos a un dataframe con labels ya definidos.

import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import numpy as np
data = {
    'Fecha_Hora'        : pd.to_datetime(df_historial['date'] + ' ' + df_historial['time']),
    'Producto_Tienda'   : df_historial['product_name'],
    'Categoria_Tienda'  : df_historial['category'],
    'Tipo_de_Movimiento': df_historial['movement_type'],
    'Cantidad'          : df_historial['quantity'],
    'Precio_Unitario'   : df_historial['price_per_unit'],
    'Stock_Minimo'      : df_historial['minimum_stock'],
    'Stock_Restante'    : df_historial['stock_after']
}



datacopy = data.copy()
df = pd.DataFrame(datacopy)

# ---------------------------------------------------------
# Calcular el flujo 
# ---------------------------------------------------------

# 1. Ordenamos por fecha para que el cálculo cronológico sea correcto
df = df.sort_values(by=['Producto_Tienda', 'Fecha_Hora'])

# 2. Creamos una columna temporal 'Cambio_Stock'
df['Cambio_Stock'] = np.where(
    df['Tipo_de_Movimiento'] == 'Salida', 
    df['Cantidad'] * -1, 
    df['Cantidad']
)

# 3. Calculamos el Stock Acumulado (Running Total) por producto
df['Stock_Calculado'] = df.groupby('Producto_Tienda')['Cambio_Stock'].cumsum()

# ---------------------------------------------------------

# 4. Calcular métricas finales
df['Total_Venta'] = df['Cantidad'] * df['Precio_Unitario']
df['Valor_Inventario'] = df['Stock_Calculado'] * df['Precio_Unitario']

# 5. Limpieza (opcional): quitamos la columna auxiliar
# df = df.drop(columns=['Cambio_Stock'])

print(df[['Fecha_Hora', 'Producto_Tienda', 'Tipo_de_Movimiento', 'Cantidad', 'Stock_Calculado']].head(10))


ventas = df.groupby('Producto_Tienda').agg({'Cantidad':'sum', 'Total_Venta':'sum'}).reset_index()
ventas = ventas.sort_values(by='Total_Venta', ascending=True)

fig1 = px.bar(ventas,
              x='Total_Venta',
              y='Producto_Tienda',
              orientation='h',
              title ='Ranking de Ventas por Producto',
              text='Cantidad',
              color_continuous_scale='Viridis'
              )

fig1.update_layout(xaxis_title='Total de Ventas',
                   yaxis_title='Producto',
                   template='plotly_white')
#fig1.show()

df['Estado_Stock'] = np.where(np.array(df['Stock_Calculado']) < np.array(df['Stock_Minimo']), 'Bajo', 'Adecuado')

colores = {'Bajo' :'red','Adecuado':'green'}
##############################################
# Gráfico de barras con alerta de stock
################################################


fig2 = px.bar(df, 
              x='Producto_Tienda', 
              y='Stock_Calculado', 
              color='Estado_Stock',
              title='Alerta de Stock (Rojo = Debajo del Mínimo)',
              color_discrete_map=colores,
              text='Stock_Calculado')

# Agregamos una línea horizontal para marcar el umbral (ejemplo visual)
fig2.add_shape(type="line", x0=-0.5, x1=5.5, y0=5, y1=5, 
               line=dict(color="Black", width=2, dash="dot"))
fig2.update_layout(yaxis_title="Unidades en Bodega")
#fig2.show()

# --- GRÁFICA 3: MAPA DE CALOR (La que faltaba) ---
# Preparamos los datos
df['Dia_Semana'] = df['Fecha_Hora'].dt.day_name()
df['Hora'] = df['Fecha_Hora'].dt.hour
dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Agrupamos
actividad = df.groupby(['Dia_Semana', 'Hora']).size().reset_index(name='Movimientos')

fig3 = px.density_heatmap(actividad, 
                          x='Dia_Semana', 
                          y='Hora', 
                          z='Movimientos', 
                          title='Mapa de Calor: Intensidad de Actividad',
                          category_orders={'Dia_Semana': dias_orden},
                          color_continuous_scale='Magma',
                          nbinsy=24) # Para que las horas se vean bien

# Ajuste visual eje Y
fig3.update_layout(yaxis=dict(tickmode='linear', dtick=1, range=[7, 19]))
fig3.show()
# --- GRÁFICA 4: CUADRANTE DE EFICIENCIA (Stock vs Ventas) ---

# 1. Preparamos los datos: Stock Actual vs Total Vendido
df_scatter = df.groupby('Producto_Tienda').agg({
    'Total_Venta': 'sum',          # Eje Y: Qué tanto se mueve el dinero 
    'Stock_Calculado': 'last',     # Eje X: Cuánto tengo 
    'Categoria_Tienda': 'first'    # Para colorear por categoría
}).reset_index()

# 2. Creamos el gráfico
fig4 = px.scatter(df_scatter, 
                  x='Stock_Calculado', 
                  y='Total_Venta',
                  color='Categoria_Tienda', # Colores por categoría
                  size='Total_Venta',       # El tamaño de la burbuja es la venta
                  hover_name='Producto_Tienda',
                  text='Producto_Tienda',
                  title='<b>Cuadrante de Eficiencia:</b> ¿Qué sobra y qué falta?',
                  template='plotly_white')

# 3. Agregamos líneas promedio para dividir en 4 cuadrantes
promedio_ventas = df_scatter['Total_Venta'].mean()
promedio_stock = df_scatter['Stock_Calculado'].mean()

fig4.add_vline(x=promedio_stock, line_dash="dot", annotation_text="Stock Promedio")
fig4.add_hline(y=promedio_ventas, line_dash="dot", annotation_text="Ventas Promedio")

# Etiquetas de los cuadrantes (Opcional, para que se entienda mejor)
# Cuadrante: Vende Mucho / Poco Stock (Peligro)
fig4.add_annotation(x=promedio_stock*0.5, y=promedio_ventas*1.5, 
                    text=" PELIGRO (Reponer)", showarrow=False, font=dict(color="red"))

# Cuadrante: Vende Poco / Mucho Stock (Exceso)
fig4.add_annotation(x=promedio_stock*1.5, y=promedio_ventas*0.5, 
                    text=" EXCESO (Ofertar)", showarrow=False, font=dict(color="gray"))

fig4.show()
# Muestra cuánto dinero hay en cada Categoría y Producto
fig5 = px.sunburst(df, 
                   path=['Categoria_Tienda', 'Producto_Tienda'], 
                   values='Valor_Inventario',
                   color='Valor_Inventario',
                   title='<b>Distribución del Capital:</b> ¿Dónde está mi dinero?',
                   color_continuous_scale='RdBu')
fig5.update_layout(yaxis=dict(tickmode='linear', dtick=1, range=[7, 19]))
fig5.show()
# Calculamos la contribución de cada producto a las ventas totales
df_abc = df.groupby('Producto_Tienda')['Total_Venta'].sum().reset_index()
df_abc = df_abc.sort_values(by='Total_Venta', ascending=False)

# Calculamos porcentaje acumulado
df_abc['Porcentaje_Acumulado'] = (df_abc['Total_Venta'].cumsum() / df_abc['Total_Venta'].sum()) * 100

# Creamos el gráfico combinado (Barras + Línea)
fig6 = go.Figure()

# Barras: Venta por producto
fig6.add_trace(go.Bar(
    x=df_abc['Producto_Tienda'], 
    y=df_abc['Total_Venta'],
    name='Venta ($)',
    marker_color='rgb(55, 83, 109)'
))

# Línea: Porcentaje acumulado
fig6.add_trace(go.Scatter(
    x=df_abc['Producto_Tienda'], 
    y=df_abc['Porcentaje_Acumulado'],
    name='% Acumulado',
    yaxis='y2',
    marker_color='rgb(255, 65, 54)'
))

fig6.update_layout(
    title='<b>Análisis ABC (Pareto):</b> El 80% de tus ingresos viene de estos productos',
    yaxis_title='Ventas ($)',
    yaxis2=dict(
        title='Porcentaje Acumulado (%)',
        overlaying='y',
        side='right',
        range=[0, 110]
    ),
    template='plotly_white'
)

# Línea del 80% (Regla de Pareto)
fig6.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Límite 80% (Clase A)", yref="y2")
fig6.show()
# Calculamos qué porcentaje de productos tienen stock BAJO
total_productos = len(df)
productos_bajos = len(df[df['Estado_Stock'] == 'Bajo'])
porcentaje_riesgo = (productos_bajos / total_productos) * 100

fig7 = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = porcentaje_riesgo,
    title = {'text': "<b>Nivel de Riesgo de Stock</b><br>(% Productos Agotándose)"},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "darkblue"},
        'steps': [
            {'range': [0, 30], 'color': "green"},  # 0-30% Riesgo bajo (Bien)
            {'range': [30, 70], 'color': "yellow"}, # 30-70% Riesgo medio
            {'range': [70, 100], 'color': "red"}   # 70-100% Riesgo alto (Mal)
        ],
        'threshold': {
            'line': {'color': "black", 'width': 4},
            'thickness': 0.75,
            'value': porcentaje_riesgo
        }
    }
))
fig7.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="KPI DE SALUD DE INVENTARIO", yref="y2")

fig7.show()