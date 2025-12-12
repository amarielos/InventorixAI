import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# OJO: import correcto dentro del paquete backend
from src.backend.obtener_historial import obtener_historial


def generar_reportes():
    df_historial = obtener_historial()

    data = {
        "Fecha_Hora": pd.to_datetime(df_historial["date"] + " " + df_historial["time"], errors="coerce"),
        "Producto_Tienda": df_historial["product_name"],
        "Categoria_Tienda": df_historial["category"],
        "Tipo_de_Movimiento": df_historial["movement_type"],
        "Cantidad": df_historial["quantity"],
        "Precio_Unitario": df_historial["price_per_unit"],
        "Stock_Minimo": df_historial["minimum_stock"],
        "Stock_Restante": df_historial["stock_after"],
    }

    df = pd.DataFrame(data).dropna(subset=["Fecha_Hora"])

    # ORDENAR
    df = df.sort_values(by=["Producto_Tienda", "Fecha_Hora"])

    # CALCULAR STOCK (nota: 'Ingreso' no es 'Salida' => suma)
    df["Cambio_Stock"] = np.where(df["Tipo_de_Movimiento"] == "Salida", -df["Cantidad"], df["Cantidad"])
    df["Stock_Calculado"] = df.groupby("Producto_Tienda")["Cambio_Stock"].cumsum()

    # METRICAS
    df["Total_Venta"] = df["Cantidad"] * df["Precio_Unitario"]
    df["Valor_Inventario"] = df["Stock_Calculado"] * df["Precio_Unitario"]

    # =======================
    # GRÁFICOS
    # =======================

    # 1. Ranking de ventas
    ventas = (
        df.groupby("Producto_Tienda")
        .agg({"Cantidad": "sum", "Total_Venta": "sum"})
        .reset_index()
        .sort_values(by="Total_Venta")
    )

    fig1 = px.bar(
        ventas,
        x="Total_Venta",
        y="Producto_Tienda",
        orientation="h",
        title="Ranking de Ventas por Producto",
        text="Cantidad",
        color_continuous_scale="Viridis",
    )

    # 2. Alerta de stock
    df["Estado_Stock"] = np.where(df["Stock_Calculado"] < df["Stock_Minimo"], "Bajo", "Adecuado")
    colores = {"Bajo": "red", "Adecuado": "green"}

    # Importante: para que no repita barras por cada movimiento, usamos el "último" estado por producto
    df_stock = (
        df.sort_values("Fecha_Hora")
        .groupby("Producto_Tienda")
        .tail(1)
        .copy()
    )

    fig2 = px.bar(
        df_stock,
        x="Producto_Tienda",
        y="Stock_Calculado",
        color="Estado_Stock",
        color_discrete_map=colores,
        title="Alerta de Stock",
        text="Stock_Calculado",
    )

    # 3. Heatmap actividad
    df["Dia_Semana"] = df["Fecha_Hora"].dt.day_name()
    df["Hora"] = df["Fecha_Hora"].dt.hour
    actividad = df.groupby(["Dia_Semana", "Hora"]).size().reset_index(name="Movimientos")

    fig3 = px.density_heatmap(
        actividad,
        x="Dia_Semana",
        y="Hora",
        z="Movimientos",
        title="Mapa de Calor",
    )

    # 4. Cuadrante eficiencia
    df_scatter = (
        df.groupby("Producto_Tienda")
        .agg({"Total_Venta": "sum", "Stock_Calculado": "last", "Categoria_Tienda": "first"})
        .reset_index()
    )

    fig4 = px.scatter(
        df_scatter,
        x="Stock_Calculado",
        y="Total_Venta",
        color="Categoria_Tienda",
        size="Total_Venta",
        hover_name="Producto_Tienda",
        text="Producto_Tienda",
        title="Cuadrante de Eficiencia",
    )

    # 5. Sunburst
    fig5 = px.sunburst(
        df,
        path=["Categoria_Tienda", "Producto_Tienda"],
        values="Valor_Inventario",
        title="Distribución del Capital",
    )

    # 6. ABC Pareto
    df_abc = df.groupby("Producto_Tienda")["Total_Venta"].sum().reset_index()
    df_abc = df_abc.sort_values(by="Total_Venta", ascending=False)
    df_abc["Porcentaje_Acumulado"] = df_abc["Total_Venta"].cumsum() / df_abc["Total_Venta"].sum() * 100

    fig6 = go.Figure()
    fig6.add_trace(go.Bar(x=df_abc["Producto_Tienda"], y=df_abc["Total_Venta"], name="Ventas"))
    fig6.add_trace(go.Scatter(
        x=df_abc["Producto_Tienda"],
        y=df_abc["Porcentaje_Acumulado"],
        name="% Acumulado",
        yaxis="y2",
        mode="lines+markers"
    ))
    fig6.update_layout(
        title="ABC Pareto",
        yaxis_title="Ventas",
        yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 110]),
    )

    # 7. Indicador riesgo
    total = len(df_stock) if len(df_stock) > 0 else 1
    bajos = len(df_stock[df_stock["Estado_Stock"] == "Bajo"])
    porcentaje = (bajos / total) * 100

    fig7 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=porcentaje,
        title={"text": "Riesgo de Stock (% productos bajo mínimo)"},
        gauge={
            "axis": {"range": [0, 100]},
            "steps": [
                {"range": [0, 30], "color": "green"},
                {"range": [30, 70], "color": "yellow"},
                {"range": [70, 100], "color": "red"},
            ],
        }
    ))

    figs = {
        "fig1_ranking_ventas": fig1,
        "fig2_alerta_stock": fig2,
        "fig3_heatmap": fig3,
        "fig4_cuadrante": fig4,
        "fig5_sunburst": fig5,
        "fig6_pareto": fig6,
        "fig7_riesgo": fig7,
    }

    return df, figs
