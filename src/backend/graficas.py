# graficas.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from src.backend.obtener_historial import obtener_historial


# =========================================================
# GENERAR DATASET BASE + FIGURAS + KPIS (SIN FILTROS)
# =========================================================
def generar_reportes():
    df_historial = obtener_historial().copy()

    df_historial["Fecha_Hora"] = pd.to_datetime(
        df_historial["datetime"],
        errors="coerce"
    )

    df = pd.DataFrame({
        "Fecha_Hora": df_historial["Fecha_Hora"],
        "Producto_Tienda": df_historial["product_name"],
        "Categoria_Tienda": df_historial["category"],
        "Tipo_de_Movimiento": df_historial["movement_type"],
        "Cantidad": df_historial["quantity"],
        "Precio_Unitario": df_historial["price_per_unit"],
        "Stock_Minimo": df_historial["minimum_stock"],
        "Stock_Real": df_historial["stock_after"],
    }).dropna(subset=["Fecha_Hora"])

    df = df.sort_values(by=["Producto_Tienda", "Fecha_Hora"])

    return df, recalcular_figuras(df), recalcular_kpis(df)


# =========================================================
# RECALCULAR KPIS (CON FILTROS)
# =========================================================
def recalcular_kpis(df):
    df = df.copy()

    df["Total_Venta"] = np.where(
        df["Tipo_de_Movimiento"] == "Salida",
        df["Cantidad"] * df["Precio_Unitario"],
        0
    )

    ventas_totales = df["Total_Venta"].sum()
    productos_distintos = df["Producto_Tienda"].nunique()

    df_stock = (
        df.groupby("Producto_Tienda")
        .tail(1)
        .copy()
    )

    df_stock["Estado_Stock"] = np.where(
        df_stock["Stock_Real"] < df_stock["Stock_Minimo"],
        "Bajo",
        "Adecuado"
    )

    productos_bajo_minimo = (df_stock["Estado_Stock"] == "Bajo").sum()
    riesgo_pct = productos_bajo_minimo / max(len(df_stock), 1) * 100

    consumo_promedio = (
        df[df["Tipo_de_Movimiento"] == "Salida"]
        .groupby("Producto_Tienda")["Cantidad"]
        .mean()
    )

    df_stock["Dias_Cobertura"] = df_stock["Stock_Real"] / consumo_promedio
    productos_criticos = df_stock[df_stock["Dias_Cobertura"] < 3].shape[0]

    return {
        "ventas_totales": ventas_totales,
        "productos_distintos": productos_distintos,
        "productos_bajo_minimo": productos_bajo_minimo,
        "riesgo_pct": riesgo_pct,
        "productos_criticos": productos_criticos,
    }


# =========================================================
# RECALCULAR FIGURAS (CON FILTROS)
# =========================================================
def recalcular_figuras(df):
    df = df.copy()

    df["Total_Venta"] = np.where(
        df["Tipo_de_Movimiento"] == "Salida",
        df["Cantidad"] * df["Precio_Unitario"],
        0
    )

    df["Valor_Inventario"] = df["Stock_Real"] * df["Precio_Unitario"]

    # ---------- Stock ----------
    df_stock = (
        df.groupby("Producto_Tienda")
        .tail(1)
        .copy()
    )

    df_stock["Estado_Stock"] = np.where(
        df_stock["Stock_Real"] < df_stock["Stock_Minimo"],
        "Bajo",
        "Adecuado"
    )

    # ---------- 1. Ranking ventas ----------
    ventas = (
        df.groupby("Producto_Tienda")["Total_Venta"]
        .sum()
        .reset_index()
        .sort_values(by="Total_Venta")
    )

    fig1 = px.bar(
        ventas,
        x="Total_Venta",
        y="Producto_Tienda",
        orientation="h",
        title="Ranking de Ventas por Producto",
        color="Total_Venta",
        color_continuous_scale="Viridis",
    )

    # ---------- 2. Alerta stock ----------
    fig2 = px.bar(
        df_stock,
        x="Producto_Tienda",
        y="Stock_Real",
        color="Estado_Stock",
        text="Stock_Real",
        title="Estado de Stock por Producto",
        color_discrete_map={"Bajo": "red", "Adecuado": "green"},
    )

    # ---------- 3. Heatmap ----------
    df["Dia_Semana"] = df["Fecha_Hora"].dt.day_name()
    df["Hora"] = df["Fecha_Hora"].dt.hour

    actividad = (
        df.groupby(["Dia_Semana", "Hora"])
        .size()
        .reset_index(name="Movimientos")
    )

    fig3 = px.density_heatmap(
        actividad,
        x="Dia_Semana",
        y="Hora",
        z="Movimientos",
        title="Mapa de Calor de Actividad",
    )

    # ---------- 4. Cuadrante ----------
    df_scatter = (
        df.groupby("Producto_Tienda")
        .agg({
            "Total_Venta": "sum",
            "Stock_Real": "last",
            "Categoria_Tienda": "first"
        })
        .reset_index()
    )

    fig4 = px.scatter(
        df_scatter,
        x="Stock_Real",
        y="Total_Venta",
        size="Total_Venta",
        color="Categoria_Tienda",
        hover_name="Producto_Tienda",
        title="Cuadrante de Eficiencia",
    )

    # ---------- 5. Sunburst ----------
    fig5 = px.sunburst(
        df,
        path=["Categoria_Tienda", "Producto_Tienda"],
        values="Valor_Inventario",
        title="Distribución del Capital en Inventario",
    )

    # ---------- 6. Pareto ----------
    df_abc = (
        df.groupby("Producto_Tienda")["Total_Venta"]
        .sum()
        .reset_index()
        .sort_values(by="Total_Venta", ascending=False)
    )

    df_abc["Porcentaje_Acumulado"] = (
        df_abc["Total_Venta"].cumsum()
        / max(df_abc["Total_Venta"].sum(), 1)
        * 100
    )

    fig6 = go.Figure()
    fig6.add_bar(x=df_abc["Producto_Tienda"], y=df_abc["Total_Venta"])
    fig6.add_scatter(
        x=df_abc["Producto_Tienda"],
        y=df_abc["Porcentaje_Acumulado"],
        yaxis="y2",
        mode="lines+markers"
    )

    fig6.update_layout(
        title="Análisis ABC (Pareto)",
        yaxis2=dict(overlaying="y", side="right", range=[0, 110]),
    )

    # ---------- 7. Riesgo ----------
    riesgo_pct = (
        (df_stock["Estado_Stock"] == "Bajo").sum()
        / max(len(df_stock), 1)
        * 100
    )

    fig7 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=riesgo_pct,
        title={"text": "Riesgo de Stock (%)"},
        gauge={"axis": {"range": [0, 100]}},
    ))

    return {
        "fig1_ranking_ventas": fig1,
        "fig2_alerta_stock": fig2,
        "fig3_heatmap": fig3,
        "fig4_cuadrante": fig4,
        "fig5_sunburst": fig5,
        "fig6_pareto": fig6,
        "fig7_riesgo": fig7,
    }

